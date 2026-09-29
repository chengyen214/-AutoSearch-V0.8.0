"""
tests/V8_0/test_r9_3_chat_api.py

AutoSearch V8

R9.3 Chat API Test
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.routes.rag import router


class TestR9ChatAPI(unittest.TestCase):
    """
    R9.3 Chat API Test。

    驗證:
        1. query
        2. urls=None
        3. urls=[...]
        4. urls=[]
        5. Empty Query
    """

    @classmethod
    def setUpClass(cls):
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        cls.client = TestClient(app)

    @patch("api.routes.rag.get_rag_query")
    def test_query_only(self, mock_get_rag_query):
        """
        未提供 urls 時，應傳入 urls=None。
        """

        mock_rag = mock_get_rag_query.return_value
        mock_rag.run.return_value = {
            "answer": "test answer",
            "sources": [],
        }

        response = self.client.post(
            "/rag/query",
            json={
                "query": "semiconductor trends",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        mock_rag.run.assert_called_once_with(
            query="semiconductor trends",
            urls=None,
        )

    @patch("api.routes.rag.get_rag_query")
    def test_url_scope(self, mock_get_rag_query):
        """
        提供 URL Scope 時，應將 URL 傳入 RAGQuery。
        """

        mock_rag = mock_get_rag_query.return_value
        mock_rag.run.return_value = {
            "answer": "test answer",
            "sources": [],
        }

        urls = [
            "https://example.com/article-1",
            "https://example.com/article-2",
        ]

        response = self.client.post(
            "/rag/query",
            json={
                "query": "article summary",
                "urls": urls,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        mock_rag.run.assert_called_once_with(
            query="article summary",
            urls=urls,
        )

    @patch("api.routes.rag.get_rag_query")
    def test_empty_scope(self, mock_get_rag_query):
        """
        urls=[] 應保持空 List，不得轉成 None。
        """

        mock_rag = mock_get_rag_query.return_value
        mock_rag.run.return_value = {
            "answer": "",
            "sources": [],
        }

        response = self.client.post(
            "/rag/query",
            json={
                "query": "article summary",
                "urls": [],
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        mock_rag.run.assert_called_once_with(
            query="article summary",
            urls=[],
        )

    @patch("api.routes.rag.get_rag_query")
    def test_url_strip(self, mock_get_rag_query):
        """
        URL 前後空白應在 API 層移除。
        """

        mock_rag = mock_get_rag_query.return_value
        mock_rag.run.return_value = {
            "answer": "test answer",
            "sources": [],
        }

        response = self.client.post(
            "/rag/query",
            json={
                "query": "article summary",
                "urls": [
                    " https://example.com/article-1 ",
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        mock_rag.run.assert_called_once_with(
            query="article summary",
            urls=[
                "https://example.com/article-1",
            ],
        )

    @patch("api.routes.rag.get_rag_query")
    def test_empty_query(self, mock_get_rag_query):
        """
        空 Query 應直接回傳錯誤，不執行 RAGQuery。
        """

        response = self.client.post(
            "/rag/query",
            json={
                "query": "   ",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json(),
            {
                "answer": "",
                "sources": [],
                "error": "Query cannot be empty.",
            },
        )

        mock_get_rag_query.assert_not_called()


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )