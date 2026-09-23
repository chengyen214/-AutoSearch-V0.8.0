"""
test_r4_5_crawl_service_integration.py

AutoSearch V7

R4.5 CrawlService Integration Test

測試：

1. CrawlService 可以正常完成 Crawl
2. HTML 可以正常取得
3. Resolved URL 可以正常保留
4. Content Hash 可以正常產生
5. Resource Downloader 可以正常執行
6. CSS Resources 可以正常回傳
7. Image Resources 可以正常回傳
8. CrawlResult 可以正常建立
9. RawHTMLRepository 可以收到 CrawlResult
10. Repository 儲存的 CrawlResult 與回傳結果相同

本測試：

- 使用 CrawlService Dependency Injection
- 不修改 CrawlService
- 不修改 Crawler
- 不修改 R1
- 不修改 R4.4
- 不連線實際 MongoDB
- 不進行實際外部下載
"""


import hashlib


from services.crawl_service import (
    CrawlService,
)


TEST_URL = (
    "https://example.com/article"
)

TEST_RESOLVED_URL = (
    "https://example.com/article/"
)

TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>R4.5 Test</title>
</head>
<body>
    <h1>R4.5 Integration Test</h1>
</body>
</html>
"""

TEST_CSS_CONTENT = (
    "body { margin: 0; }"
)

TEST_IMAGE_CONTENT = (
    b"\x89PNG\r\n\x1a\nTEST_IMAGE"
)

TEST_CSS_URL = (
    "https://example.com/style.css"
)

TEST_IMAGE_URL = (
    "https://example.com/image.png"
)


class FakeSearchResult:
    """
    最小 SearchResult 測試物件。
    """

    def __init__(
        self,
        url,
    ):
        self.url = url
        self.keyword = None
        self.target_language = None


class FakeRawHTMLRepository:
    """
    測試用 RawHTMLRepository。

    不實際連線 MongoDB。
    """

    def __init__(self):
        self.saved_results = []

    def save_crawl_result(
        self,
        crawl_result,
    ):
        self.saved_results.append(
            crawl_result
        )

        return "test-raw-html-id"


def test_r4_5_crawl_service_integration():
    """
    R4.5 CrawlService Integration Test。
    """

    print()
    print(
        "R4.5 CrawlService Integration Test"
    )
    print()

    downloader_calls = []
    resolver_calls = []
    resource_downloader_calls = []

    def fake_downloader(
        url,
    ):
        downloader_calls.append(
            url
        )

        return TEST_HTML

    def fake_url_resolver(
        url,
    ):
        resolver_calls.append(
            url
        )

        return TEST_RESOLVED_URL

    def fake_resource_downloader(
        html,
        base_url,
    ):
        resource_downloader_calls.append(
            {
                "html": html,
                "base_url": base_url,
            }
        )

        return {
            "css": [
                {
                    "url": TEST_CSS_URL,
                    "content": TEST_CSS_CONTENT,
                    "content_hash": hashlib.sha256(
                        TEST_CSS_CONTENT.encode(
                            "utf-8"
                        )
                    ).hexdigest(),
                    "mime_type": "text/css",
                    "file_size": len(
                        TEST_CSS_CONTENT.encode(
                            "utf-8"
                        )
                    ),
                }
            ],
            "images": [
                {
                    "url": TEST_IMAGE_URL,
                    "data": TEST_IMAGE_CONTENT,
                    "content_hash": hashlib.sha256(
                        TEST_IMAGE_CONTENT
                    ).hexdigest(),
                    "mime_type": "image/png",
                    "file_size": len(
                        TEST_IMAGE_CONTENT
                    ),
                }
            ],
        }

    repository = (
        FakeRawHTMLRepository()
    )

    service = CrawlService(
        downloader=fake_downloader,
        url_resolver=fake_url_resolver,
        resource_downloader=(
            fake_resource_downloader
        ),
        raw_html_repository=repository,
        save_raw_html=True,
    )

    search_result = FakeSearchResult(
        TEST_URL
    )

    result = service.crawl_result(
        search_result
    )

    expected_hash = (
        hashlib.sha256(
            TEST_HTML.encode(
                "utf-8"
            )
        ).hexdigest()
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
        "Downloader Called",
        downloader_calls == [
            TEST_URL
        ],
    )

    check(
        "Raw HTML Returned",
        result.html == TEST_HTML,
    )

    check(
        "URL Resolver Called",
        resolver_calls == [
            TEST_URL
        ],
    )

    check(
        "Resolved URL Preserved",
        result.resolved_url
        == TEST_RESOLVED_URL,
    )

    check(
        "Content Hash Generated",
        result.content_hash
        == expected_hash,
    )

    check(
        "Resource Downloader Called",
        len(
            resource_downloader_calls
        ) == 1,
    )

    check(
        "Resource Downloader Received HTML",
        resource_downloader_calls[0][
            "html"
        ] == TEST_HTML,
    )

    check(
        "Resource Downloader Received Resolved URL",
        resource_downloader_calls[0][
            "base_url"
        ] == TEST_RESOLVED_URL,
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
        ) == 1,
    )

    check(
        "RawHTMLRepository Save Called",
        len(
            repository.saved_results
        ) == 1,
    )

    check(
        "Repository Saved Same CrawlResult",
        repository.saved_results[0]
        is result,
    )

    check(
        "CrawlResult Success Property",
        service.is_success(result),
    )

    print()

    print(
        f"Saved Results : "
        f"{len(repository.saved_results)}"
    )

    print(
        f"CSS Resources : "
        f"{len(result.resources.get('css', []))}"
    )

    print(
        f"Image Resources : "
        f"{len(result.resources.get('images', []))}"
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