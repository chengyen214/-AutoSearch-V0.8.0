"""
tests/V8_0/test_r9_5_search_scope_real.py

AutoSearch V8

R9.5 Search Scope Integration Test

測試：
    Composite Archive Search API
    Pagination
    Full Search Scope Collection

使用：
    python -m unittest tests.V8_0.test_r9_5_search_scope_real
"""

import unittest

from fastapi.testclient import TestClient

from api.main import app


SEARCH_API = "/archive/search/api"


class TestR95SearchScopeReal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _get_page(
        self,
        page,
        page_size
    ):
        response = self.client.get(
            SEARCH_API,
            params={
                "page": page,
                "page_size": page_size,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "application/json",
            response.headers.get(
                "content-type",
                "",
            ),
        )

        data = response.json()

        self.assertIsInstance(
            data,
            dict,
        )

        self.assertIn(
            "results",
            data,
        )

        self.assertIn(
            "total",
            data,
        )

        self.assertIn(
            "page",
            data,
        )

        self.assertIn(
            "page_size",
            data,
        )

        self.assertIsInstance(
            data["results"],
            list,
        )

        return data

    @staticmethod
    def _extract_urls(results):
        urls = []

        for item in results:

            if not isinstance(
                item,
                dict,
            ):
                continue

            url = item.get(
                "url"
            )

            if not isinstance(
                url,
                str,
            ):
                url = item.get(
                    "article_url"
                )

            if not isinstance(
                url,
                str,
            ):
                continue

            url = url.strip()

            if not url:
                continue

            urls.append(
                url
            )

        return urls

    def test_real_search_api_pagination(self):
        first_page = self._get_page(
            page=1,
            page_size=20,
        )

        total = int(
            first_page["total"]
        )

        self.assertGreater(
            total,
            0,
            "Archive Search API returned 0 results.",
        )

        self.assertEqual(
            first_page["page"],
            1,
        )

        self.assertEqual(
            first_page["page_size"],
            20,
        )

        self.assertLessEqual(
            len(first_page["results"]),
            20,
        )

    def test_real_search_scope_fetch_uses_100_page_size(self):
        first_page = self._get_page(
            page=1,
            page_size=20,
        )

        total = int(
            first_page["total"]
        )

        if total <= 100:
            self.skipTest(
                "Real archive contains 100 or fewer results; "
                "multi-page pagination cannot be verified."
            )

        page_one = self._get_page(
            page=1,
            page_size=100,
        )

        self.assertEqual(
            page_one["page"],
            1,
        )

        self.assertEqual(
            page_one["page_size"],
            100,
        )

        self.assertEqual(
            len(page_one["results"]),
            100,
        )

        total_pages = (
            total + 100 - 1
        ) // 100

        self.assertGreater(
            total_pages,
            1,
        )

        all_urls = []

        for page in range(
            1,
            total_pages + 1,
        ):

            data = self._get_page(
                page=page,
                page_size=100,
            )

            all_urls.extend(
                self._extract_urls(
                    data["results"]
                )
            )

        unique_urls = list(
            dict.fromkeys(
                all_urls
            )
        )

        self.assertGreater(
            len(all_urls),
            100,
        )

        self.assertGreater(
            len(unique_urls),
            100,
        )

    def test_real_search_scope_does_not_use_display_page_size(self):
        display_page = self._get_page(
            page=1,
            page_size=20,
        )

        total = int(
            display_page["total"]
        )

        if total <= 100:
            self.skipTest(
                "Real archive contains 100 or fewer results; "
                "display page size mismatch cannot be verified."
            )

        display_urls = self._extract_urls(
            display_page["results"]
        )

        scope_page = self._get_page(
            page=1,
            page_size=100,
        )

        scope_urls = self._extract_urls(
            scope_page["results"]
        )

        self.assertLessEqual(
            len(display_urls),
            20,
        )

        self.assertEqual(
            scope_page["page"],
            1,
        )

        self.assertEqual(
            scope_page["page_size"],
            100,
        )

        self.assertEqual(
            len(scope_urls),
            100,
        )

        self.assertGreater(
            len(scope_urls),
            len(display_urls),
        )

    def test_real_search_scope_collects_all_pages(self):
        first_page = self._get_page(
            page=1,
            page_size=20,
        )

        total = int(
            first_page["total"]
        )

        if total <= 100:
            self.skipTest(
                "Real archive contains 100 or fewer results; "
                "full multi-page scope cannot be verified."
            )

        total_pages = (
            total + 100 - 1
        ) // 100

        collected = []

        for page in range(
            1,
            total_pages + 1,
        ):

            data = self._get_page(
                page=page,
                page_size=100,
            )

            self.assertEqual(
                data["page"],
                page,
            )

            self.assertEqual(
                data["page_size"],
                100,
            )

            collected.extend(
                self._extract_urls(
                    data["results"]
                )
            )

        self.assertGreaterEqual(
            len(collected),
            total,
        )

        unique_urls = list(
            dict.fromkeys(
                collected
            )
        )

        self.assertGreater(
            len(unique_urls),
            100,
        )

    def test_real_search_scope_page_navigation_keeps_scope_source(self):
        first_page = self._get_page(
            page=1,
            page_size=20,
        )

        total = int(
            first_page["total"]
        )

        if total <= 20:
            self.skipTest(
                "Real archive contains 20 or fewer results."
            )

        page_one_urls = self._extract_urls(
            first_page["results"]
        )

        second_page = self._get_page(
            page=2,
            page_size=20,
        )

        second_page_urls = self._extract_urls(
            second_page["results"]
        )

        self.assertEqual(
            second_page["page"],
            2,
        )

        self.assertLessEqual(
            len(second_page_urls),
            20,
        )

        self.assertNotEqual(
            page_one_urls,
            second_page_urls,
        )


if __name__ == "__main__":
    unittest.main()