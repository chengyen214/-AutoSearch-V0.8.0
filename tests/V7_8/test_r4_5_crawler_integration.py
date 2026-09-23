"""
test_r4_5_crawler_integration.py

AutoSearch V7

R4.5 Crawler Integration Test

測試：

1. CrawlService 可以正常完成 Crawl
2. HTML 可以正常取得
3. Resolved URL 可以保留
4. Content Hash 可以產生
5. CSS Resource 可以正常回傳
6. Image Resource 可以正常回傳
7. CSS Resource 收到可重用 Session
8. Image Resource 收到 RetrievalContext
9. CSS / Image 使用同一個 RetrievalContext
10. CSS 使用 Site Profile Best Strategy
11. Image 使用 Site Profile Best Strategy
12. CSS Retrieval 可以從 crawler.py 進入 R1
13. Image Retrieval 可以從 crawler.py 進入 R1

本測試：

- 使用 CrawlService Dependency Injection
- 使用真正的 crawler.download_resources()
- 不修改 R1
- 不修改 R4.4
- 不寫入 MongoDB
- 不進行實際外部 Resource Download
"""


from crawler.crawler import (
    download_resources,
)

from crawler.retrieval.css_retrieval import (
    CSSRetrievalResult,
)

from crawler.retrieval.image_retrieval import (
    ImageRetrievalResult,
)

from services.crawl_service import (
    CrawlService,
)


TEST_URL = "https://example.com/"

TEST_RESOLVED_URL = (
    "https://example.com/"
)

TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link
        rel="stylesheet"
        href="/style-1.css"
    >
</head>
<body>
    <img src="/image-1.png">
    <img src="/image-2.png">
    <img src="/image-3.png">
</body>
</html>
"""

TEST_CSS_URL = (
    "https://example.com/style-1.css"
)

TEST_IMAGE_URLS = [
    "https://example.com/image-1.png",
    "https://example.com/image-2.png",
    "https://example.com/image-3.png",
]

TEST_CSS_CONTENT = (
    "body { margin: 0; }"
)

TEST_IMAGE_CONTENT = (
    b"\x89PNG\r\n\x1a\nTEST_IMAGE"
)

TEST_CSS_STRATEGY = "referer"

TEST_IMAGE_STRATEGY = "cookie_session"


class FakeSearchResult:
    """
    最小 SearchResult 測試物件。
    """

    def __init__(
        self,
        url,
    ):
        self.url = url


class FakeSiteProfile:
    """
    最小 SiteProfile 測試物件。
    """

    html_best_strategy = "http"

    css_best_strategy = (
        TEST_CSS_STRATEGY
    )

    image_best_strategy = (
        TEST_IMAGE_STRATEGY
    )


class FakeRawHTMLRepository:
    """
    測試用 RawHTMLRepository。

    本測試不驗證 MongoDB。
    """

    def __init__(self):
        self.saved = []

    def save_crawl_result(
        self,
        crawl_result,
    ):
        self.saved.append(
            crawl_result
        )

        return "test-mongo-id"


class FakeRetrievalContext:
    """
    測試用 RetrievalContext。

    模擬 crawler.py 建立單一
    RetrievalContext，並讓 CSS
    取得 Session、Image 取得
    RetrievalContext。
    """

    def __init__(self):
        self.sessions = {}

    def get_session(
        self,
        strategy="http",
    ):
        """
        建立並重用 Strategy Session。
        """

        if strategy not in self.sessions:
            self.sessions[strategy] = (
                object()
            )

        return self.sessions[strategy]

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return None


def _build_css_result(
    url,
    strategy,
):
    """
    建立 CSS RetrievalResult。
    """

    return CSSRetrievalResult(
        success=True,
        strategy=strategy,
        url=url,
        final_url=url,
        css=TEST_CSS_CONTENT,
        status_code=200,
        content_type="text/css",
        content_size=len(
            TEST_CSS_CONTENT.encode(
                "utf-8"
            )
        ),
        content_hash=(
            "3e67b4a9505b24600272f1ce6b6776c4ae2ebde88f76559d4a2a51f602d800c4"
        ),
        elapsed_time=0.01,
        error=None,
    )


def _build_image_result(
    url,
    strategy,
):
    """
    建立 Image RetrievalResult。
    """

    return ImageRetrievalResult(
        success=True,
        strategy=strategy,
        url=url,
        final_url=url,
        content=TEST_IMAGE_CONTENT,
        status_code=200,
        content_type="image/png",
        content_size=len(
            TEST_IMAGE_CONTENT
        ),
        content_hash=(
            "test-image-hash"
        ),
        elapsed_time=0.01,
        error=None,
    )


def test_r4_5_crawl_service_integration():
    """
    R4.5 CrawlService → crawler.py
    → RetrievalContext Integration Test。
    """

    print()
    print(
        "R4.5 Crawler Integration Test"
    )
    print()

    css_sessions = []
    image_contexts = []

    css_strategies = []
    image_strategies = []

    css_retrieval_called = []
    image_retrieval_called = []

    created_contexts = []

    def fake_downloader(
        url,
    ):
        if url != TEST_URL:
            raise AssertionError(
                "Unexpected download URL: "
                f"{url}"
            )

        return TEST_HTML

    def fake_url_resolver(
        url,
    ):
        return TEST_RESOLVED_URL

    def fake_get_site_profile(
        url,
    ):
        if url != TEST_RESOLVED_URL:
            raise AssertionError(
                "Unexpected profile URL: "
                f"{url}"
            )

        return FakeSiteProfile()

    def fake_retrieval_context():
        """
        建立測試用 RetrievalContext。
        """

        context = (
            FakeRetrievalContext()
        )

        created_contexts.append(
            context
        )

        return context

    def fake_retrieve_css(
        url,
        strategy="http",
        **kwargs,
    ):
        """
        Mock R1 CSS Retrieval。

        R1.2 CSS 使用 session=
        傳入可重用 requests.Session。
        """

        session = kwargs.get(
            "session"
        )

        css_sessions.append(
            session
        )

        css_strategies.append(
            strategy
        )

        css_retrieval_called.append(
            url
        )

        return _build_css_result(
            url,
            strategy,
        )

    def fake_retrieve_image(
        url,
        strategy="http",
        **kwargs,
    ):
        """
        Mock R1 Image Retrieval。

        R1.3 Image 支援
        retrieval_context。
        """

        retrieval_context = kwargs.get(
            "retrieval_context"
        )

        image_contexts.append(
            retrieval_context
        )

        image_strategies.append(
            strategy
        )

        image_retrieval_called.append(
            url
        )

        return _build_image_result(
            url,
            strategy,
        )

    import crawler.crawler as crawler_module

    original_get_site_profile = (
        crawler_module._get_site_profile
    )

    original_retrieval_context = (
        crawler_module.RetrievalContext
    )

    original_retrieve_css = (
        crawler_module.retrieve_css
    )

    original_retrieve_image = (
        crawler_module.retrieve_image
    )

    crawler_module._get_site_profile = (
        fake_get_site_profile
    )

    crawler_module.RetrievalContext = (
        fake_retrieval_context
    )

    crawler_module.retrieve_css = (
        fake_retrieve_css
    )

    crawler_module.retrieve_image = (
        fake_retrieve_image
    )

    repository = (
        FakeRawHTMLRepository()
    )

    try:
        service = CrawlService(
            downloader=fake_downloader,
            url_resolver=fake_url_resolver,
            resource_downloader=(
                download_resources
            ),
            raw_html_repository=repository,
            save_raw_html=False,
        )

        search_result = FakeSearchResult(
            TEST_URL
        )

        result = service.crawl_result(
            search_result
        )

    finally:
        crawler_module._get_site_profile = (
            original_get_site_profile
        )

        crawler_module.RetrievalContext = (
            original_retrieval_context
        )

        crawler_module.retrieve_css = (
            original_retrieve_css
        )

        crawler_module.retrieve_image = (
            original_retrieve_image
        )

    passed = 0
    failed = 0

    def check(
        name,
        condition,
    ):
        nonlocal passed
        nonlocal failed

        if condition:
            print(
                f"PASS: {name}"
            )
            passed += 1

        else:
            print(
                f"FAIL: {name}"
            )
            failed += 1

    check(
        "CrawlService Crawl Success",
        result.success is True,
    )

    check(
        "Raw HTML Returned",
        result.html == TEST_HTML,
    )

    check(
        "Resolved URL Preserved",
        result.resolved_url
        == TEST_RESOLVED_URL,
    )

    check(
        "Content Hash Generated",
        result.content_hash
        == service.generate_content_hash(
            TEST_HTML
        ),
    )

    check(
        "CSS Resources Returned",
        len(
            result.resources.get(
                "css",
                [],
            )
        ) == 1,
    )

    check(
        "Image Resources Returned",
        len(
            result.resources.get(
                "images",
                [],
            )
        ) == 3,
    )

    check(
        "CSS Session Exists",
        len(css_sessions) == 1
        and css_sessions[0] is not None,
    )

    check(
        "Image RetrievalContexts Exist",
        len(image_contexts) == 3
        and all(
            context is not None
            for context in image_contexts
        ),
    )

    expected_css_session = None

    if created_contexts:
        expected_css_session = (
            created_contexts[0].get_session(
                TEST_CSS_STRATEGY
            )
        )

    check(
        "CSS Session Comes From RetrievalContext",
        len(css_sessions) == 1
        and created_contexts
        and css_sessions[0]
        is expected_css_session,
    )

    check(
        "CSS/Image Share Same RetrievalContext",
        len(created_contexts) == 1
        and len(image_contexts) == 3
        and all(
            context is created_contexts[0]
            for context in image_contexts
        ),
    )

    check(
        "CSS Strategy Uses Site Profile",
        css_strategies == [
            TEST_CSS_STRATEGY
        ],
    )

    check(
        "Image Strategy Uses Site Profile",
        image_strategies
        == [
            TEST_IMAGE_STRATEGY,
            TEST_IMAGE_STRATEGY,
            TEST_IMAGE_STRATEGY,
        ],
    )

    check(
        "CSS Retrieval Reached R1",
        css_retrieval_called
        == [TEST_CSS_URL],
    )

    check(
        "Image Retrieval Reached R1",
        image_retrieval_called
        == TEST_IMAGE_URLS,
    )

    print()

    if css_sessions:
        print(
            "CSS Session : "
            f"{id(css_sessions[0])}"
        )

    if image_contexts:
        print(
            "Image RetrievalContexts : "
            f"{[id(context) for context in image_contexts]}"
        )

    if created_contexts:
        print(
            "RetrievalContext : "
            f"{id(created_contexts[0])}"
        )

    print()
    print(
        f"PASS: {passed}"
    )
    print(
        f"FAIL: {failed}"
    )
    print(
        f"TOTAL: {passed + failed}"
    )

    assert failed == 0


if __name__ == "__main__":
    test_r4_5_crawl_service_integration()