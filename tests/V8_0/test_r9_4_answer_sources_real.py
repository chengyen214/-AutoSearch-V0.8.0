"""
tests/V8_0/test_r9_4_answer_sources_real.py

AutoSearch V8

R9.4 Real Answer + Sources Integration Test
"""

import unittest

from rag.rag_query import RAGQuery


class TestR9AnswerSourcesReal(unittest.TestCase):
    """
    R9.4 Real Answer + Sources Integration Test。

    使用實際 RAGQuery、ChromaDB、Embedding Model
    與 LLM Pipeline。
    """

    @classmethod
    def setUpClass(cls):
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

    def _assert_answer_sources(
        self,
        result,
        scoped_urls=None,
    ):
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

        answer = result["answer"]
        sources = result["sources"]

        self.assertIsInstance(
            answer,
            str,
        )

        self.assertTrue(
            answer.strip()
        )

        self.assertIsInstance(
            sources,
            list,
        )

        self.assertTrue(
            sources
        )

        for source in sources:
            self.assertIsInstance(
                source,
                dict,
            )

            self.assertIn(
                "source_index",
                source,
            )

            self.assertIn(
                "title",
                source,
            )

            self.assertIn(
                "url",
                source,
            )

            self.assertIsInstance(
                source["source_index"],
                int,
            )

            self.assertIsInstance(
                source["url"],
                str,
            )

            self.assertTrue(
                source["url"].strip()
            )

            if scoped_urls is not None:
                self.assertIn(
                    source["url"],
                    scoped_urls,
                )

    def test_real_answer_sources_all_archive(self):
        """
        urls=None 應實際執行完整 RAG Pipeline
        並回傳 Answer + Sources。
        """

        result = self.rag.run(
            query="What are the main topics?",
            urls=None,
        )

        self._assert_answer_sources(
            result
        )

    def test_real_answer_sources_scoped_archive(self):
        """
        指定 URL 時，Sources 應來自指定 Archive 範圍。
        """

        result = self.rag.run(
            query="What is this article about?",
            urls=[
                self.test_url,
            ],
        )

        self._assert_answer_sources(
            result,
            scoped_urls=[
                self.test_url,
            ],
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )