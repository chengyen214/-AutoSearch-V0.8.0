"""
crawler.py

AutoSearch V5

Web Downloader

功能：

1. requests 下載 HTML
2. timeout
3. retry
4. delay
5. redirect
6. encoding 修正
7. SSL Certificate Error fallback
8. SSL fallback host cache
9. CSS Resource Download
10. Image Resource Download
11. Resource URL Resolution
12. Resource Content Hash
13. Resource Metadata

Backward Compatibility：

    download(url)
        ↓
    HTML string

新增：

    download_resources(
        html,
        base_url
    )
        ↓
    {
        "css": [],
        "images": []
    }

Site Profile Integration：

    URL
        ↓
    SiteProfileService
        ↓
    Site Profile
        ↓
    Best Strategy
        ↓
    R1 Retrieval

注意：

    crawler.py 負責：

        Site Profile Integration
        Resource Extraction
        Resource Metadata
        Resource Hash
        Backward Compatibility

    R1 負責：

        HTML Retrieval
        CSS Retrieval
        Image Retrieval
        SSL fallback
        Session
        Referer
        Cookie Session
        Browser

    不負責：

        MongoDB
        CrawlResult
        Article
        Parser
        Archive
        AI
"""

import hashlib
import time

from concurrent.futures import (
    ThreadPoolExecutor,
)

from urllib.parse import (
    urljoin,
    urlparse,
)

import requests

from bs4 import (
    BeautifulSoup,
)

from urllib3.exceptions import (
    InsecureRequestWarning,
)

import urllib3

from config.settings import (
    TIMEOUT,
    CRAWL_DELAY,
    CSS_CONCURRENCY,
    IMAGE_CONCURRENCY,
)

from crawler.retrieval.html_retrieval import (
    retrieve_html,
)

from crawler.retrieval.css_retrieval import (
    retrieve_css,
)

from crawler.retrieval.image_retrieval import (
    retrieve_image,
)

from crawler.retrieval.retrieval_context import (
    RetrievalContext,
)

from crawler.retrieval.site_profile_service import (
    SiteProfileService,
)


DEFAULT_HEADERS = {
    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),
    "Accept-Language":
    "zh-TW,zh;q=0.9,en;q=0.8",
}


_SSL_FALLBACK_HOSTS = set()


def _get_hostname(
    url,
):
    """
    取得 URL Host，例如 https://www.nuk.edu.tw/ → www.nuk.edu.tw。
    若 URL 無法解析，回傳 None。
    """

    if not url:
        return None

    try:
        hostname = urlparse(
            str(url)
        ).hostname

    except Exception:
        return None

    if not hostname:
        return None

    return hostname.lower()


def _is_ssl_fallback_host(
    url,
):
    """
    判斷 Host 是否已經進入 SSL fallback cache。
    """

    hostname = _get_hostname(
        url
    )

    if not hostname:
        return False

    return (
        hostname
        in _SSL_FALLBACK_HOSTS
    )


def _mark_ssl_fallback_host(
    url,
):
    """
    將 Host 加入 SSL fallback cache；只記錄 Host，不永久保存。
    """

    hostname = _get_hostname(
        url
    )

    if not hostname:
        return

    if hostname in _SSL_FALLBACK_HOSTS:
        return

    _SSL_FALLBACK_HOSTS.add(
        hostname
    )

    print(
        "SSL fallback host cached: "
        f"{hostname}"
    )


def _clear_ssl_fallback_cache():
    """
    清除 SSL fallback cache，主要提供測試與 Debug 使用。
    """

    _SSL_FALLBACK_HOSTS.clear()


def _disable_ssl_warning():
    """
    停用 urllib3 的 InsecureRequestWarning，只在 SSL fallback verify=False 時使用。
    """

    urllib3.disable_warnings(
        InsecureRequestWarning
    )


def _get_site_profile(
    url,
):
    """
    取得 URL 對應的 Site Profile。

    SiteProfileService 會：

        1. 根據 URL 建立 Site Identity
        2. 使用 base_url 查詢 MongoDB
        3. 已存在時直接回傳
        4. 不存在時建立 Site Profile 並保存
    """

    service = SiteProfileService()

    return service.get_or_create(
        url
    )


def resolve_url(
    url,
    headers=None,
):
    """
    取得真正新聞網址。

    此函式保留原本 API。

    R3 後主要 HTML 下載流程由 R1 Retrieval 處理 Redirect
    與 SSL fallback。

    處理：

        - Google redirect
        - 新聞轉址
        - 短網址

    SSL：

        正常：

            verify=True

        SSL Certificate Error：

            verify=False

        同一 Host：

            使用 SSL fallback cache

    Returns：

        最終 URL
    """

    if headers is None:
        headers = DEFAULT_HEADERS

    if _is_ssl_fallback_host(
        url
    ):
        try:
            _disable_ssl_warning()

            response = requests.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=TIMEOUT,
                verify=False,
            )

            return response.url

        except requests.RequestException:
            return url

    try:
        response = requests.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=TIMEOUT,
            verify=True,
        )

        return response.url

    except requests.exceptions.SSLError as e:
        print(
            "SSL 憑證驗證失敗，"
            "Resolve URL 啟用 SSL fallback:"
        )

        print(e)

        _mark_ssl_fallback_host(
            url
        )

        try:
            _disable_ssl_warning()

            response = requests.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=TIMEOUT,
                verify=False,
            )

            print(
                "SSL fallback redirect 成功"
            )

            return response.url

        except requests.RequestException as fallback_error:
            print(
                "SSL fallback redirect 失敗:"
            )

            print(
                fallback_error
            )

            return url

    except requests.RequestException:
        return url


def fix_encoding(
    response,
):
    """
    修正網站編碼，避免 UTF-8 → ISO-8859-1 → 中文亂碼。
    """

    encoding = response.apparent_encoding

    if encoding:
        response.encoding = encoding

    return response.text


def _download_request(
    url,
    headers,
):
    """
    保留原本 HTTP Download API。

    R3 後實際 HTML/CSS/Image Retrieval
    由 R1 Retrieval 模組負責。
    """

    verify_ssl = not _is_ssl_fallback_host(
        url
    )

    if not verify_ssl:
        _disable_ssl_warning()

    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT,
        verify=verify_ssl,
    )

    response.raise_for_status()

    return response


def _download_ssl_fallback(
    url,
    headers,
):
    """
    保留原本 SSL Certificate Error fallback API。
    """

    _mark_ssl_fallback_host(
        url
    )

    print(
        "啟用 SSL fallback:"
    )

    print(
        f"URL: {url}"
    )

    _disable_ssl_warning()

    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT,
        verify=False,
    )

    response.raise_for_status()

    return response


def generate_resource_hash(
    data,
):
    """
    產生 Resource SHA-256，支援 bytes 與 str，回傳 64 字元 hexadecimal SHA-256。
    """

    if data is None:
        raise ValueError(
            "data cannot be None"
        )

    if isinstance(
        data,
        str,
    ):
        data = data.encode(
            "utf-8"
        )

    elif not isinstance(
        data,
        bytes,
    ):
        data = bytes(
            data
        )

    return hashlib.sha256(
        data
    ).hexdigest()


def normalize_resource_url(
    resource_url,
    base_url,
):
    """
    將 HTML 中的 Resource URL 轉換成絕對 URL。
    """

    if not resource_url:
        return None

    resource_url = str(
        resource_url
    ).strip()

    if not resource_url:
        return None

    if resource_url.startswith(
        (
            "data:",
            "javascript:",
            "mailto:",
            "tel:",
            "#",
        )
    ):
        return None

    return urljoin(
        base_url,
        resource_url,
    )


def extract_css_urls(
    html,
    base_url,
):
    """
    從 HTML 擷取 CSS URL，主要處理 <link rel="stylesheet" href="...">。
    Returns: list[str]
    """

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    css_urls = []
    seen = set()

    for tag in soup.find_all(
        "link"
    ):
        rel = tag.get(
            "rel"
        )

        href = tag.get(
            "href"
        )

        if not href:
            continue

        if isinstance(
            rel,
            list,
        ):
            rel_values = [
                str(
                    value
                ).lower()
                for value in rel
            ]

        else:
            rel_values = [
                str(
                    rel
                ).lower()
            ]

        if "stylesheet" not in rel_values:
            continue

        css_url = normalize_resource_url(
            href,
            base_url,
        )

        if not css_url:
            continue

        if css_url in seen:
            continue

        seen.add(
            css_url
        )

        css_urls.append(
            css_url
        )

    return css_urls


def extract_image_urls(
    html,
    base_url,
):
    """
    從 HTML 擷取圖片 URL，支援 img src、data-src、data-original、data-lazy-src、data-image 與 srcset。
    """

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    image_urls = []
    seen = set()

    for tag in soup.find_all(
        "img"
    ):
        attributes = (
            "src",
            "data-src",
            "data-original",
            "data-lazy-src",
            "data-image",
        )

        for attribute in attributes:
            value = tag.get(
                attribute
            )

            image_url = normalize_resource_url(
                value,
                base_url,
            )

            if not image_url:
                continue

            if image_url in seen:
                continue

            seen.add(
                image_url
            )

            image_urls.append(
                image_url
            )

        srcset = tag.get(
            "srcset"
        )

        if srcset:
            for item in srcset.split(
                ","
            ):
                item = item.strip()

                if not item:
                    continue

                image_url = item.split(
                    " "
                )[0].strip()

                image_url = normalize_resource_url(
                    image_url,
                    base_url,
                )

                if not image_url:
                    continue

                if image_url in seen:
                    continue

                seen.add(
                    image_url
                )

                image_urls.append(
                    image_url
                )

    return image_urls


def download_css_resource(
    url,
    headers=None,
    strategy="http",
    retrieval_context=None,
):
    """
    使用 Site Profile 指定的 CSS Retrieval Strategy
    下載單一 CSS Resource，失敗回傳 None。
    """

    if not url:
        return None

    if headers is None:
        headers = DEFAULT_HEADERS

    try:
        kwargs = {
            "strategy": strategy,
        }

        if strategy != "browser":
            if retrieval_context is not None:
                kwargs["session"] = (
                    retrieval_context.get_session(
                        strategy
                    )
                )

        result = retrieve_css(
            url,
            **kwargs,
        )

    except Exception as e:
        print(
            "CSS download failed:"
        )

        print(
            f"URL: {url}"
        )

        print(e)

        return None

    if not result.success:
        print(
            "CSS download failed:"
        )

        print(
            f"URL: {url}"
        )

        if result.error:
            print(
                result.error
            )

        return None

    content = result.css

    if not content:
        return None

    mime_type = (
        result.content_type
        or "text/css"
    )

    mime_type = mime_type.split(
        ";"
    )[0].strip()

    content_hash = (
        result.content_hash
        or generate_resource_hash(
            content
        )
    )

    file_size = (
        result.content_size
        or len(
            content.encode(
                "utf-8"
            )
        )
    )

    time.sleep(
        CRAWL_DELAY
    )

    return {
        "url":
            result.final_url
            or url,
        "content":
            content,
        "content_hash":
            content_hash,
        "mime_type":
            mime_type,
        "file_size":
            file_size,
    }


def download_image_resource(
    url,
    headers=None,
    strategy="http",
    retrieval_context=None,
):
    """
    使用 Site Profile 指定的 Image Retrieval Strategy
    下載單一 Image Resource，失敗回傳 None。
    """

    if not url:
        return None

    if headers is None:
        headers = DEFAULT_HEADERS

    try:
        if retrieval_context is None:
            result = retrieve_image(
                url,
                strategy=strategy,
            )
        else:
            result = retrieve_image(
                url,
                strategy=strategy,
                retrieval_context=retrieval_context,
            )

    except Exception as e:
        print(
            "Image download failed:"
        )

        print(
            f"URL: {url}"
        )

        print(e)

        return None

    if not result.success:
        print(
            "Image download failed:"
        )

        print(
            f"URL: {url}"
        )

        if result.error:
            print(
                result.error
            )

        return None

    mime_type = (
        result.content_type
        or ""
    )

    mime_type = mime_type.split(
        ";"
    )[0].strip().lower()

    if not mime_type.startswith(
        "image/"
    ):
        print(
            "非 Image Resource:"
        )

        print(
            f"URL: {url}"
        )

        print(
            f"MIME: {mime_type}"
        )

        return None

    data = result.content

    if not data:
        return None

    content_hash = (
        result.content_hash
        or generate_resource_hash(
            data
        )
    )

    file_size = (
        result.content_size
        or len(
            data
        )
    )

    time.sleep(
        CRAWL_DELAY
    )

    return {
        "url":
            result.final_url
            or url,
        "data":
            data,
        "content_hash":
            content_hash,
        "mime_type":
            mime_type,
        "file_size":
            file_size,
    }


def _download_css_resources(
    css_urls,
    headers,
    strategy,
    retrieval_context=None,
):
    """
    依 CSS_CONCURRENCY 下載 CSS Resources。
    """

    if not css_urls:
        return []

    concurrency = max(
        1,
        int(
            CSS_CONCURRENCY
        ),
    )

    def download_one(
        css_url,
    ):
        try:
            if retrieval_context is None:
                return download_css_resource(
                    css_url,
                    headers=headers,
                    strategy=strategy,
                )

            return download_css_resource(
                css_url,
                headers=headers,
                strategy=strategy,
                retrieval_context=retrieval_context,
            )

        except Exception as e:
            print(
                "CSS resource processing failed:"
            )

            print(
                f"URL: {css_url}"
            )

            print(e)

            return None

    if concurrency == 1:
        return [
            download_one(
                css_url
            )
            for css_url in css_urls
        ]

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        futures = [
            executor.submit(
                download_one,
                css_url,
            )
            for css_url in css_urls
        ]

        return [
            future.result()
            for future in futures
        ]


def _download_image_resources(
    image_urls,
    headers,
    strategy,
    retrieval_context=None,
):
    """
    依 IMAGE_CONCURRENCY 下載 Image Resources。
    """

    if not image_urls:
        return []

    concurrency = max(
        1,
        int(
            IMAGE_CONCURRENCY
        ),
    )

    def download_one(
        image_url,
    ):
        try:
            if retrieval_context is None:
                return download_image_resource(
                    image_url,
                    headers=headers,
                    strategy=strategy,
                )

            return download_image_resource(
                image_url,
                headers=headers,
                strategy=strategy,
                retrieval_context=retrieval_context,
            )

        except Exception as e:
            print(
                "Image resource processing failed:"
            )

            print(
                f"URL: {image_url}"
            )

            print(e)

            return None

    if concurrency == 1:
        return [
            download_one(
                image_url
            )
            for image_url in image_urls
        ]

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:
        futures = [
            executor.submit(
                download_one,
                image_url,
            )
            for image_url in image_urls
        ]

        return [
            future.result()
            for future in futures
        ]


def download_resources(
    html,
    base_url,
    headers=None,
):
    """
    從 HTML 擷取並下載 CSS 與 Image Resources。

    CSS 與 Image 使用 Site Profile
    各自指定的 Best Strategy。

    Resource 下載失敗不會讓 HTML Crawl 失敗。

    RetrievalContext 在整個 Resource Download
    工作期間共用，讓同一 Worker 可以重複使用 Session。
    """

    resources = {
        "css": [],
        "images": [],
    }

    if not html:
        return resources

    if not base_url:
        return resources

    if headers is None:
        headers = DEFAULT_HEADERS

    profile = _get_site_profile(
        base_url
    )

    css_strategy = (
        profile.css_best_strategy
        or "http"
    )

    image_strategy = (
        profile.image_best_strategy
        or "http"
    )

    css_urls = extract_css_urls(
        html,
        base_url,
    )

    with RetrievalContext() as retrieval_context:
        css_results = _download_css_resources(
            css_urls,
            headers,
            css_strategy,
            retrieval_context,
        )

        for resource in css_results:
            if resource is not None:
                resources[
                    "css"
                ].append(
                    resource
                )

        image_urls = extract_image_urls(
            html,
            base_url,
        )

        image_results = _download_image_resources(
            image_urls,
            headers,
            image_strategy,
            retrieval_context,
        )

        for resource in image_results:
            if resource is not None:
                resources[
                    "images"
                ].append(
                    resource
                )

    return resources


def download(
    url,
    headers=None,
    retry=3,
):
    """
    使用 Site Profile 的 HTML Best Strategy
    下載 HTML。

    保持原本 API：

        download(url)
            ↓
        HTML string

    R1 負責：

        Redirect
        Retry
        SSL fallback
        HTTP
        Session
        Referer
        Cookie session
        Browser
    """

    if not url:
        return None

    if headers is None:
        headers = DEFAULT_HEADERS

    try:
        profile = _get_site_profile(
            url
        )

    except Exception as e:
        print(
            "Site Profile lookup failed:"
        )

        print(e)

        return None

    strategy = (
        profile.html_best_strategy
        or "http"
    )

    print(
        "Site Profile HTML Strategy: "
        f"{strategy}"
    )

    for count in range(
        retry
    ):
        try:
            result = retrieve_html(
                url,
                strategy=strategy,
                headers=headers,
                retry=1,
            )

            if not result.success:
                print(
                    f"HTML Retrieval failed "
                    f"{count + 1}/{retry}"
                )

                if result.error:
                    print(
                        result.error
                    )

                if count < retry - 1:
                    time.sleep(
                        2
                    )

                continue

            html = result.html

            if not html:
                print(
                    "下載HTML為空"
                )

                return None

            if not html.strip():
                print(
                    "下載HTML為空"
                )

                return None

            time.sleep(
                CRAWL_DELAY
            )

            return html

        except Exception as e:
            print(
                f"下載失敗 "
                f"{count + 1}/{retry}"
            )

            print(e)

            if count < retry - 1:
                time.sleep(
                    2
                )

    return None


__all__ = [
    "DEFAULT_HEADERS",
    "resolve_url",
    "fix_encoding",
    "download",
    "download_resources",
    "extract_css_urls",
    "extract_image_urls",
    "download_css_resource",
    "download_image_resource",
    "generate_resource_hash",
    "normalize_resource_url",
]