"""
tests/V8_0/test_r9_7_integration.py

AutoSearch V8

R9.7 Integration Test

驗證:
    Archive Search
        ↓
    Search Scope
        ↓
    RAG Chat API
        ↓
    Scoped Retrieval
        ↓
    Answer + Sources

使用:
    python -m unittest tests.V8_0.test_r9_7_integration -v
"""

import unittest

from fastapi.testclient import TestClient

from api.main import app


SEARCH_API = "/archive/search/api"
RAG_API = "/rag/query"


class TestR97Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _search(
        self,
        keyword=None,
        page=1,
        page_size=20,
    ):
        params = {
            "page": page,
            "page_size": page_size,
        }

        if keyword is not None:
            params["keyword"] = keyword

        response = self.client.get(
            SEARCH_API,
            params=params,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        content_type = response.headers.get(
            "content-type",
            "",
        )

        self.assertIn(
            "application/json",
            content_type,
        )

        data = response.json()

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

        return data

    def _extract_urls(self, results):
        urls = []

        for item in results:
            if not isinstance(item, dict):
                continue

            url = item.get("url")

            if not isinstance(url, str):
                url = item.get("article_url")

            if not isinstance(url, str):
                continue

            url = url.strip()

            if url:
                urls.append(url)

        return list(dict.fromkeys(urls))

    def _chat(
        self,
        query,
        urls=None,
    ):
        payload = {
            "query": query,
            "urls": urls,
        }

        response = self.client.post(
            RAG_API,
            json=payload,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        content_type = response.headers.get(
            "content-type",
            "",
        )

        self.assertIn(
            "application/json",
            content_type,
        )

        data = response.json()

        self.assertIn(
            "answer",
            data,
        )

        self.assertIn(
            "sources",
            data,
        )

        return data

    def test_search_to_chat_scoped_archive(self):
        search_data = self._search(
            page=1,
            page_size=20,
        )

        total = int(
            search_data["total"]
        )

        if total <= 0:
            self.skipTest(
                "Real archive contains no search results."
            )

        urls = self._extract_urls(
            search_data["results"]
        )

        if not urls:
            self.skipTest(
                "Real archive search results contain no usable URLs."
            )

        chat_data = self._chat(
            query="請整理這些資料的主要內容。",
            urls=urls,
        )

        self.assertIsInstance(
            chat_data["answer"],
            str,
        )

        self.assertIsInstance(
            chat_data["sources"],
            list,
        )

        for source in chat_data["sources"]:
            self.assertIsInstance(
                source,
                dict,
            )

            source_url = source.get(
                "url"
            )

            if source_url:
                self.assertIn(
                    source_url,
                    urls,
                )

    def test_search_empty_scope_to_chat(self):
        search_data = self._search(
            keyword="__R9_7_NO_MATCH__",
            page=1,
            page_size=20,
        )

        self.assertEqual(
            search_data["total"],
            0,
        )

        urls = self._extract_urls(
            search_data["results"]
        )

        self.assertEqual(
            urls,
            [],
        )

        chat_data = self._chat(
            query="請回答搜尋結果中的內容。",
            urls=urls,
        )

        self.assertEqual(
            chat_data["answer"],
            "",
        )

        self.assertEqual(
            chat_data["sources"],
            [],
        )

    def test_chat_all_archive_without_search(self):
        chat_data = self._chat(
            query="請整理 Archive 中的主要內容。",
            urls=None,
        )

        self.assertIsInstance(
            chat_data["answer"],
            str,
        )

        self.assertIsInstance(
            chat_data["sources"],
            list,
        )

        if not chat_data["sources"]:
            self.skipTest(
                "Real archive RAG returned no sources."
            )

        for source in chat_data["sources"]:
            self.assertIsInstance(
                source,
                dict,
            )

            self.assertTrue(
                source.get("url")
            )

    def test_search_scope_preserved_across_pages(self):
        first_page = self._search(
            page=1,
            page_size=20,
        )

        total = int(
            first_page["total"]
        )

        if total <= 20:
            self.skipTest(
                "Real archive contains 20 or fewer results; "
                "page navigation cannot be verified."
            )

        first_scope = self._extract_urls(
            first_page["results"]
        )

        second_page = self._search(
            page=2,
            page_size=20,
        )

        second_page_urls = self._extract_urls(
            second_page["results"]
        )

        if not second_page_urls:
            self.skipTest(
                "Second search page contains no usable URLs."
            )

        full_scope = list(
            dict.fromkeys(
                first_scope +
                second_page_urls
            )
        )

        self.assertGreater(
            len(full_scope),
            0,
        )

        chat_data = self._chat(
            query="請整理這些搜尋結果的內容。",
            urls=full_scope,
        )

        self.assertIsInstance(
            chat_data["answer"],
            str,
        )

        self.assertIsInstance(
            chat_data["sources"],
            list,
        )

        for source in chat_data["sources"]:
            source_url = source.get(
                "url"
            )

            if source_url:
                self.assertIn(
                    source_url,
                    full_scope,
                )

    def test_scoped_sources_are_not_outside_search_scope(self):
        search_data = self._search(
            page=1,
            page_size=20,
        )

        urls = self._extract_urls(
            search_data["results"]
        )

        if not urls:
            self.skipTest(
                "Real archive search results contain no usable URLs."
            )

        chat_data = self._chat(
            query="請整理搜尋結果中的資訊。",
            urls=urls,
        )

        sources = chat_data["sources"]

        for source in sources:
            source_url = source.get(
                "url"
            )

            if source_url:
                self.assertIn(
                    source_url,
                    urls,
                )


if __name__ == "__main__":
    unittest.main()