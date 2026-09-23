"""
image_retrieval.py

AutoSearch V7

R1.3 Image Retrieval

功能：

1. HTTP Image Retrieval
2. Session Image Retrieval
3. Referer Image Retrieval
4. Cookie Session Image Retrieval
5. SSL Fallback Image Retrieval
6. Browser Image Retrieval
7. Image Content Validation
8. Image Content Hash
9. Image Metadata

原則：

    已知 Image URL 後，
    使用不同 Retrieval Strategy
    直接下載原始圖片。

不進行：

    - 圖片縮放
    - 圖片壓縮
    - JPEG Quality 調整
    - 格式轉換
    - Image Discovery
    - HTML Parsing
    - CSS Parsing

Backward Compatibility：

    retrieve_image(url)
        ↓
    HTTP Image Retrieval
"""

from __future__ import annotations

import hashlib
import time

from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
import urllib3
from requests.exceptions import SSLError

from crawler.retrieval.retrieval_context import (
    RetrievalContext,
)


DEFAULT_TIMEOUT = 15


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "image/avif,image/webp,image/apng,"
        "image/svg+xml,image/*,*/*;q=0.8"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


_SSL_FALLBACK_HOSTS = set()


@dataclass
class ImageRetrievalResult:
    """
    Image Retrieval 結果。
    """

    success: bool
    strategy: str
    url: str

    final_url: Optional[str] = None
    content: Optional[bytes] = None

    status_code: Optional[int] = None
    content_type: Optional[str] = None

    content_size: int = 0
    content_hash: Optional[str] = None

    elapsed_time: float = 0.0
    error: Optional[str] = None


def _get_hostname(url: str) -> str:
    """
    取得 URL hostname。
    """

    try:
        return (
            urlparse(url).hostname
            or ""
        ).lower()

    except Exception:
        return ""


def _is_ssl_fallback_host(url: str) -> bool:
    """
    判斷 hostname 是否已進入
    SSL fallback cache。
    """

    hostname = _get_hostname(url)

    return hostname in _SSL_FALLBACK_HOSTS


def _mark_ssl_fallback_host(url: str) -> None:
    """
    將 hostname 加入 SSL fallback cache。
    """

    hostname = _get_hostname(url)

    if hostname:
        _SSL_FALLBACK_HOSTS.add(hostname)


def _generate_content_hash(
    content: bytes,
) -> str:
    """
    產生 Image SHA-256 content hash。
    """

    return hashlib.sha256(
        content
    ).hexdigest()


def _is_image_signature(
    content: bytes,
) -> bool:
    """
    判斷常見 Image binary signature。
    """

    if not content:
        return False

    signatures = (
        b"\xff\xd8\xff",
        b"\x89PNG\r\n\x1a\n",
        b"GIF87a",
        b"GIF89a",
        b"RIFF",
        b"BM",
        b"II*\x00",
        b"MM\x00*",
        b"\x00\x00\x01\x00",
    )

    if any(
        content.startswith(signature)
        for signature in signatures
    ):
        return True

    stripped = content.lstrip()

    return (
        stripped.startswith(b"<svg")
        or stripped.startswith(b"<?xml")
    )


def _validate_image_response(
    response,
) -> bool:
    """
    驗證 Image Response。
    """

    if hasattr(response, "status_code"):
        status_code = response.status_code

        content_type = (
            response.headers.get(
                "Content-Type",
                "",
            )
            .lower()
        )

        content = response.content

    else:
        status_code = response.status

        content_type = (
            response.headers.get(
                "content-type",
                "",
            )
            .lower()
        )

        content = response.body()

    if status_code >= 400:
        return False

    if content_type.startswith("image/"):
        return bool(content)

    return _is_image_signature(content)


def _build_result(
    *,
    success: bool,
    strategy: str,
    url: str,
    response=None,
    content: Optional[bytes] = None,
    elapsed_time: float = 0.0,
    error: Optional[str] = None,
) -> ImageRetrievalResult:
    """
    建立 ImageRetrievalResult。
    """

    if response is None:
        return ImageRetrievalResult(
            success=success,
            strategy=strategy,
            url=url,
            elapsed_time=elapsed_time,
            error=error,
        )

    final_url = response.url

    if hasattr(response, "status_code"):
        status_code = response.status_code

        content_type = response.headers.get(
            "Content-Type"
        )

    else:
        status_code = response.status

        content_type = response.headers.get(
            "content-type"
        )

    if content is None:
        if hasattr(response, "content"):
            content = response.content
        else:
            content = response.body()

    content_size = (
        len(content)
        if content
        else 0
    )

    content_hash = (
        _generate_content_hash(content)
        if content
        else None
    )

    return ImageRetrievalResult(
        success=success,
        strategy=strategy,
        url=url,
        final_url=final_url,
        content=content,
        status_code=status_code,
        content_type=content_type,
        content_size=content_size,
        content_hash=content_hash,
        elapsed_time=elapsed_time,
        error=error,
    )


def _retrieve_request(
    *,
    client,
    url: str,
    strategy: str,
    timeout: int,
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    verify: bool = True,
) -> ImageRetrievalResult:
    """
    Requests-based Image Retrieval 共用實作。
    """

    start_time = time.perf_counter()

    request_headers = dict(
        DEFAULT_HEADERS
    )

    if headers:
        request_headers.update(headers)

    try:
        response = client.get(
            url,
            headers=request_headers,
            cookies=cookies,
            timeout=timeout,
            allow_redirects=True,
            verify=verify,
        )

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        content = response.content

        if not _validate_image_response(
            response
        ):
            return _build_result(
                success=False,
                strategy=strategy,
                url=url,
                response=response,
                content=content,
                elapsed_time=elapsed_time,
                error=(
                    "Response is not a valid "
                    "image resource"
                ),
            )

        if not content:
            return _build_result(
                success=False,
                strategy=strategy,
                url=url,
                response=response,
                content=content,
                elapsed_time=elapsed_time,
                error="Image content is empty",
            )

        return _build_result(
            success=True,
            strategy=strategy,
            url=url,
            response=response,
            content=content,
            elapsed_time=elapsed_time,
        )

    except SSLError as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy=strategy,
            url=url,
            elapsed_time=elapsed_time,
            error=f"SSL error: {exc}",
        )

    except requests.Timeout as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy=strategy,
            url=url,
            elapsed_time=elapsed_time,
            error=(
                f"Request timeout: {exc}"
            ),
        )

    except Exception as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy=strategy,
            url=url,
            elapsed_time=elapsed_time,
            error=str(exc),
        )


def retrieve_image_http(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retrieval_context: Optional[
        RetrievalContext
    ] = None,
) -> ImageRetrievalResult:
    """
    HTTP Image Retrieval。
    """

    if retrieval_context is not None:
        session = retrieval_context.get_session(
            "http"
        )

        return _retrieve_request(
            client=session,
            url=url,
            strategy="http",
            timeout=timeout,
        )

    with requests.Session() as session:
        return _retrieve_request(
            client=session,
            url=url,
            strategy="http",
            timeout=timeout,
        )


def retrieve_image_session(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retrieval_context: Optional[
        RetrievalContext
    ] = None,
) -> ImageRetrievalResult:
    """
    Session Image Retrieval。
    """

    start_time = time.perf_counter()

    try:
        if retrieval_context is not None:
            session = retrieval_context.get_session(
                "session"
            )

            session.headers.update(
                DEFAULT_HEADERS
            )

            response = session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
            )

            elapsed_time = (
                time.perf_counter()
                - start_time
            )

            content = response.content

            if not _validate_image_response(
                response
            ):
                return _build_result(
                    success=False,
                    strategy="session",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error=(
                        "Response is not a valid "
                        "image resource"
                    ),
                )

            if not content:
                return _build_result(
                    success=False,
                    strategy="session",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error="Image content is empty",
                )

            return _build_result(
                success=True,
                strategy="session",
                url=url,
                response=response,
                content=content,
                elapsed_time=elapsed_time,
            )

        with requests.Session() as session:
            session.headers.update(
                DEFAULT_HEADERS
            )

            response = session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
            )

            elapsed_time = (
                time.perf_counter()
                - start_time
            )

            content = response.content

            if not _validate_image_response(
                response
            ):
                return _build_result(
                    success=False,
                    strategy="session",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error=(
                        "Response is not a valid "
                        "image resource"
                    ),
                )

            if not content:
                return _build_result(
                    success=False,
                    strategy="session",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error="Image content is empty",
                )

            return _build_result(
                success=True,
                strategy="session",
                url=url,
                response=response,
                content=content,
                elapsed_time=elapsed_time,
            )

    except Exception as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy="session",
            url=url,
            elapsed_time=elapsed_time,
            error=str(exc),
        )


def retrieve_image_referer(
    url: str,
    *,
    referer: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retrieval_context: Optional[
        RetrievalContext
    ] = None,
) -> ImageRetrievalResult:
    """
    Referer Image Retrieval。
    """

    if referer is None:
        parsed = urlparse(url)

        referer = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    if retrieval_context is not None:
        client = retrieval_context.get_session(
            "referer"
        )
    else:
        client = requests

    return _retrieve_request(
        client=client,
        url=url,
        strategy="referer",
        timeout=timeout,
        headers={
            "Referer": referer,
        },
    )


def retrieve_image_cookie_session(
    url: str,
    *,
    cookies: Optional[Dict[str, str]] = None,
    referer: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retrieval_context: Optional[
        RetrievalContext
    ] = None,
) -> ImageRetrievalResult:
    """
    Cookie Session Image Retrieval。
    """

    if referer is None:
        parsed = urlparse(url)

        referer = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    if retrieval_context is not None:
        session = retrieval_context.get_session(
            "cookie_session"
        )

        return _retrieve_request(
            client=session,
            url=url,
            strategy="cookie_session",
            timeout=timeout,
            headers={
                "Referer": referer,
            },
            cookies=cookies,
        )

    with requests.Session() as session:
        return _retrieve_request(
            client=session,
            url=url,
            strategy="cookie_session",
            timeout=timeout,
            headers={
                "Referer": referer,
            },
            cookies=cookies,
        )


def retrieve_image_ssl_fallback(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retrieval_context: Optional[
        RetrievalContext
    ] = None,
) -> ImageRetrievalResult:
    """
    SSL Fallback Image Retrieval。
    """

    if retrieval_context is not None:
        client = retrieval_context.get_session(
            "ssl_fallback"
        )
    else:
        client = requests

    if _is_ssl_fallback_host(url):
        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )

        return _retrieve_request(
            client=client,
            url=url,
            strategy="ssl_fallback",
            timeout=timeout,
            verify=False,
        )

    result = _retrieve_request(
        client=client,
        url=url,
        strategy="ssl_fallback",
        timeout=timeout,
        verify=True,
    )

    if result.success:
        return result

    if (
        result.error
        and result.error.startswith(
            "SSL error:"
        )
    ):
        _mark_ssl_fallback_host(url)

        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )

        return _retrieve_request(
            client=client,
            url=url,
            strategy="ssl_fallback",
            timeout=timeout,
            verify=False,
        )

    return result


def retrieve_image_browser(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
) -> ImageRetrievalResult:
    """
    Browser Image Retrieval。

    使用 Playwright
    APIRequestContext
    取得圖片原始 bytes。
    """

    start_time = time.perf_counter()

    browser = None
    context = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
            )

            context = browser.new_context(
                user_agent=DEFAULT_HEADERS[
                    "User-Agent"
                ],
                extra_http_headers={
                    "Accept": DEFAULT_HEADERS[
                        "Accept"
                    ],
                    "Accept-Language": DEFAULT_HEADERS[
                        "Accept-Language"
                    ],
                },
            )

            response = context.request.get(
                url,
                timeout=timeout * 1000,
                max_redirects=10,
            )

            elapsed_time = (
                time.perf_counter()
                - start_time
            )

            content = response.body()

            if not _validate_image_response(
                response
            ):
                return _build_result(
                    success=False,
                    strategy="browser",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error=(
                        "Response is not a valid "
                        "image resource"
                    ),
                )

            if not content:
                return _build_result(
                    success=False,
                    strategy="browser",
                    url=url,
                    response=response,
                    content=content,
                    elapsed_time=elapsed_time,
                    error="Image content is empty",
                )

            return _build_result(
                success=True,
                strategy="browser",
                url=url,
                response=response,
                content=content,
                elapsed_time=elapsed_time,
            )

    except PlaywrightTimeoutError as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy="browser",
            url=url,
            elapsed_time=elapsed_time,
            error=(
                f"Browser timeout: {exc}"
            ),
        )

    except Exception as exc:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return ImageRetrievalResult(
            success=False,
            strategy="browser",
            url=url,
            elapsed_time=elapsed_time,
            error=str(exc),
        )

    finally:
        if context is not None:
            try:
                context.dispose()
            except Exception:
                pass

        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass


IMAGE_RETRIEVAL_STRATEGIES = {
    "http": retrieve_image_http,
    "session": retrieve_image_session,
    "referer": retrieve_image_referer,
    "cookie_session": retrieve_image_cookie_session,
    "ssl_fallback": retrieve_image_ssl_fallback,
    "browser": retrieve_image_browser,
}


def get_image_retrieval_strategies():
    """
    取得 Image Retrieval Strategy Registry。
    """

    return dict(
        IMAGE_RETRIEVAL_STRATEGIES
    )


def retrieve_image(
    url: str,
    strategy: str = "http",
    **kwargs,
) -> ImageRetrievalResult:
    """
    Image Retrieval 統一入口。

    預設：

        retrieve_image(url)

    等同：

        retrieve_image(
            url,
            strategy="http",
        )
    """

    retrieval_function = (
        IMAGE_RETRIEVAL_STRATEGIES.get(
            strategy
        )
    )

    if retrieval_function is None:
        return ImageRetrievalResult(
            success=False,
            strategy=strategy,
            url=url,
            error=(
                f"Unknown image retrieval "
                f"strategy: {strategy}"
            ),
        )

    return retrieval_function(
        url,
        **kwargs,
    )


__all__ = [
    "ImageRetrievalResult",
    "retrieve_image_http",
    "retrieve_image_session",
    "retrieve_image_referer",
    "retrieve_image_cookie_session",
    "retrieve_image_ssl_fallback",
    "retrieve_image_browser",
    "get_image_retrieval_strategies",
    "retrieve_image",
]