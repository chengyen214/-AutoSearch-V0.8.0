"""
tests/V8_0/test_r9_3_chat_api_real.py

AutoSearch V8

R9.3 Real Chat API Integration Test
"""

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.rag import router
from rag.rag_query import RAGQuery


class TestR9ChatAPIReal(unittest.TestCase):
    """
    R9.3 Real Chat API Integration Test。

    使用實際 FastAPI、RAGQuery、ChromaDB、Embedding Model
    與 LLM Pipeline。
    """

    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)

        cls.client = TestClient(app)

        cls.rag = RAGQuery()

        collection = (
            cls.rag.retrieval_context
            .retriever
            .chroma_retrieval
            .collection
        )

        data = collection.get(
            include=[
                "metadatas",
            ]
        )

        metadatas = (
            data.get("metadatas")
            if data is not None
            else None
        )

        if not metadatas:
            raise unittest.SkipTest(
                "ChromaDB collection contains no data."
            )

        cls.test_url = None

        for metadata in metadatas:
            if not isinstance(
                metadata,
                dict,
            ):
                continue

            url = metadata.get("url")

            if (
                isinstance(url, str)
                and url.strip()
            ):
                cls.test_url = url.strip()
                break

        if cls.test_url is None:
            raise unittest.SkipTest(
                "No document with metadata['url'] "
                "was found in ChromaDB."
            )

    def test_real_chat_all_archive(self):
        """
        urls=None 應實際執行完整 RAG Chat Pipeline。
        """

        response = self.client.post(
            "/rag/query",
            json={
                "query": "What are the main topics?",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        result = response.json()

        self.assertIsInstance(
            result,
            dict,
        )

        self.assertIn(
            "answer",
            result,
        )

        self.assertIn(
            "sources",
            result,
        )

    def test_real_chat_scoped_archive(self):
        """
        指定 URL 時，應實際執行 URL Scoped RAG Chat。
        """

        response = self.client.post(
            "/rag/query",
            json={
                "query": "What is this article about?",
                "urls": [
                    self.test_url,
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        result = response.json()

        self.assertIsInstance(
            result,
            dict,
        )

        self.assertIn(
            "answer",
            result,
        )

        self.assertIn(
            "sources",
            result,
        )

    def test_real_chat_empty_scope(self):
        """
        urls=[] 應實際通過 API，但不進行 Retrieval。
        """

        response = self.client.post(
            "/rag/query",
            json={
                "query": "What are the main topics?",
                "urls": [],
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        result = response.json()

        self.assertIsInstance(
            result,
            dict,
        )

        self.assertIn(
            "answer",
            result
        )

        self.assertIn(
            "sources",
            result,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )