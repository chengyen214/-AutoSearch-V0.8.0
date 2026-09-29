"""
tests/V8_0/test_r9_2_scoped_retrieval_real.py
AutoSearch V8

R9.2 Real ChromaDB Integration Test
"""

import unittest

from rag.chroma.collection import (
    ChromaCollection,
)

from rag.retriever.chroma_retrieval import (
    ChromaDBRetrieval,
)


class TestR9ScopedRetrievalReal(unittest.TestCase):
    """
    R9.2 Real ChromaDB Integration Test。

    使用目前專案實際 ChromaDB 與實際 Embedding Model。
    """

    @classmethod
    def setUpClass(cls):
        cls.chroma_collection = ChromaCollection()

        cls.collection = (
            cls.chroma_collection.get_collection()
        )

        cls.retrieval = ChromaDBRetrieval(
            chroma_collection=(
                cls.chroma_collection
            )
        )

        data = cls.collection.get(
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

    def test_real_scope_none(self):
        """
        urls=None 應使用實際 ChromaDB 進行一般 Retrieval。
        """

        result = self.retrieval.retrieve(
            "semiconductor",
            urls=None,
        )

        self.assertIsInstance(
            result,
            dict,
        )

        self.assertIn(
            "ids",
            result,
        )

        self.assertIn(
            "metadatas",
            result,
        )

    def test_real_scope_url(self):
        """
        使用實際 ChromaDB 中存在的 URL 進行 Scoped Retrieval。
        """

        result = self.retrieval.retrieve(
            "semiconductor",
            urls=[
                self.test_url,
            ],
        )

        metadatas = result.get(
            "metadatas",
            [[]],
        )

        if not metadatas or not metadatas[0]:
            self.skipTest(
                "No retrieval result returned for "
                f"URL: {self.test_url}"
            )

        for metadata in metadatas[0]:
            self.assertIsInstance(
                metadata,
                dict,
            )

            self.assertEqual(
                metadata.get("url"),
                self.test_url,
            )

    def test_real_scope_empty(self):
        """
        urls=[] 應直接回傳空結果。
        """

        result = self.retrieval.retrieve(
            "semiconductor",
            urls=[],
        )

        self.assertEqual(
            result,
            {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            },
        )


if __name__ == "__main__":
    unittest.main()