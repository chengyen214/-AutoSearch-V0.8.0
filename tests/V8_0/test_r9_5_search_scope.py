"""
tests/V8_0/test_r9_5_search_scope.py

AutoSearch V8

R9.5 Search Scope Integration Test
"""

import unittest


def extract_archive_search_scope(items):
    """
    模擬 search.html 的 URL extraction。
    """

    return [
        url.strip()
        for item in items
        for url in [
            item.get("url", item.get("article_url"))
        ]
        if isinstance(url, str) and url.strip()
    ]


def collect_all_search_scope(pages):
    """
    模擬 search.html 跨 Pagination 收集全部 Search Result URL。
    """

    scope = []

    for items in pages:
        scope.extend(
            extract_archive_search_scope(
                items
            )
        )

    return list(
        dict.fromkeys(scope)
    )


class TestR95SearchScope(unittest.TestCase):

    def test_search_not_executed(self):
        """
        未執行 Search 時，scope 應為 None。
        """

        archive_search_scope = None

        self.assertIsNone(
            archive_search_scope
        )

    def test_search_with_results(self):
        """
        Search 有結果時，scope 應包含全部 Search Result URL。
        """

        pages = [
            [
                {
                    "title": "Article 1",
                    "url": "https://example.com/article-1",
                },
                {
                    "title": "Article 2",
                    "url": "https://example.com/article-2",
                },
            ]
        ]

        archive_search_scope = (
            collect_all_search_scope(
                pages
            )
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/article-1",
                "https://example.com/article-2",
            ],
        )

    def test_search_empty_results(self):
        """
        Search 0 筆時，scope 應為 []，不能 fallback 成 None。
        """

        pages = [[]]

        archive_search_scope = (
            collect_all_search_scope(
                pages
            )
        )

        self.assertEqual(
            archive_search_scope,
            [],
        )

    def test_article_url_fallback(self):
        """
        沒有 url 時，應使用 article_url。
        """

        pages = [
            [
                {
                    "title": "Article",
                    "article_url": "https://example.com/article",
                }
            ]
        ]

        archive_search_scope = (
            collect_all_search_scope(
                pages
            )
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/article",
            ],
        )

    def test_empty_or_invalid_urls_are_removed(self):
        """
        空 URL、None 與非字串 URL 不應進入 scope。
        """

        items = [
            {
                "url": "",
            },
            {
                "url": "   ",
            },
            {
                "url": None,
            },
            {
                "url": 123,
            },
            {
                "url": " https://example.com/article ",
            },
        ]

        archive_search_scope = (
            collect_all_search_scope(
                [items]
            )
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/article",
            ],
        )

    def test_scope_contains_all_search_pages(self):
        """
        Scope 應包含整次 Search 的所有 Pagination 結果。
        """

        page_1 = [
            {
                "url": "https://example.com/page-1",
            },
            {
                "url": "https://example.com/page-2",
            },
        ]

        page_2 = [
            {
                "url": "https://example.com/page-3",
            },
            {
                "url": "https://example.com/page-4",
            },
        ]

        page_3 = [
            {
                "url": "https://example.com/page-5",
            },
        ]

        archive_search_scope = (
            collect_all_search_scope(
                [
                    page_1,
                    page_2,
                    page_3,
                ]
            )
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/page-1",
                "https://example.com/page-2",
                "https://example.com/page-3",
                "https://example.com/page-4",
                "https://example.com/page-5",
            ],
        )

    def test_scope_does_not_change_when_page_changes(self):
        """
        Pagination 改變時，Chatbot scope 不應跟著改變。
        """

        page_1 = [
            {
                "url": "https://example.com/page-1",
            },
            {
                "url": "https://example.com/page-2",
            },
        ]

        page_2 = [
            {
                "url": "https://example.com/page-3",
            },
            {
                "url": "https://example.com/page-4",
            },
        ]

        archive_search_scope = (
            collect_all_search_scope(
                [
                    page_1,
                    page_2,
                ]
            )
        )

        scope_before_page_change = list(
            archive_search_scope
        )

        current_page = page_2

        self.assertEqual(
            current_page,
            page_2,
        )

        self.assertEqual(
            archive_search_scope,
            scope_before_page_change,
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/page-1",
                "https://example.com/page-2",
                "https://example.com/page-3",
                "https://example.com/page-4",
            ],
        )

    def test_scope_collects_more_than_100_results(self):
        """
        Search 超過 100 筆時，scope 應包含所有頁面的 URL。
        """

        pages = []

        for page_number in range(3):
            page = []

            start = page_number * 100 + 1
            end = start + 100

            for index in range(start, end):
                page.append(
                    {
                        "url": (
                            f"https://example.com/article-{index}"
                        )
                    }
                )

            pages.append(page)

        archive_search_scope = (
            collect_all_search_scope(
                pages
            )
        )

        self.assertEqual(
            len(archive_search_scope),
            300,
        )

        self.assertEqual(
            archive_search_scope[0],
            "https://example.com/article-1",
        )

        self.assertEqual(
            archive_search_scope[-1],
            "https://example.com/article-300",
        )

    def test_duplicate_urls_are_removed(self):
        """
        多個 Pagination 出現相同 URL 時，scope 應去重。
        """

        page_1 = [
            {
                "url": "https://example.com/article-1",
            },
            {
                "url": "https://example.com/article-2",
            },
        ]

        page_2 = [
            {
                "url": "https://example.com/article-2",
            },
            {
                "url": "https://example.com/article-3",
            },
        ]

        archive_search_scope = (
            collect_all_search_scope(
                [
                    page_1,
                    page_2,
                ]
            )
        )

        self.assertEqual(
            archive_search_scope,
            [
                "https://example.com/article-1",
                "https://example.com/article-2",
                "https://example.com/article-3",
            ],
        )

    def test_reset_scope(self):
        """
        Reset Search 後，scope 應回到 None。
        """

        archive_search_scope = [
            "https://example.com/article"
        ]

        archive_search_scope = None

        self.assertIsNone(
            archive_search_scope
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )