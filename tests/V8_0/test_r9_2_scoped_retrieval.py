"""
tests/V8_0/test_r9_2_scoped_retrieval.py
AutoSearch V8

R9.2 Scoped RAG Retrieval Test
"""

import unittest

from rag.retrieval_context import (
    RetrievalContext,
)

from rag.retriever.retriever import (
    RAGRetriever,
)

from rag.retriever.chroma_retrieval import (
    ChromaDBRetrieval,
)

from rag.retriever.top_k import (
    TopKRetrieval,
)

from rag.retriever.retrieval_result import (
    RetrievalResultBuilder,
)


class FakeQueryEmbedding:
    """
    測試用 QueryEmbedding。
    """

    def get_dimension(self):
        return 768

    def embed(self, query):
        return [0.0] * 768


class FakeChromaCollection:
    """
    測試用 ChromaDB Collection。
    """

    def __init__(self):
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)

        return {
            "ids": [
                [
                    "doc_1::chunk_0",
                ]
            ],
            "documents": [
                [
                    "test document",
                ]
            ],
            "metadatas": [
                [
                    {
                        "document_id": "doc_1",
                        "url": "https://example.com/article",
                    }
                ]
            ],
            "distances": [
                [
                    0.1,
                ]
            ],
        }


class FakeChromaCollectionWrapper:
    """
    測試用 RAG-4 ChromaCollection。
    """

    def __init__(self, collection):
        self.collection = collection

    def get_collection(self):
        return self.collection


class FakeScopedRetriever:
    """
    測試 RAGRetriever 是否正確傳遞 urls。
    """

    def __init__(self):
        self.calls = []

    def search(self, query, urls=None):
        self.calls.append(
            {
                "query": query,
                "urls": urls,
            }
        )

        return []


class FakeContextBuilder:
    """
    測試 RetrievalContext 的 ContextBuilder。
    """

    def build(self, retrieval_results):
        return retrieval_results


class TestChromaDBRetrievalScope(unittest.TestCase):
    """
    測試 R9.2 ChromaDB URL Scope。
    """

    def setUp(self):
        self.collection = FakeChromaCollection()

        self.retrieval = ChromaDBRetrieval(
            chroma_collection=(
                FakeChromaCollectionWrapper(
                    self.collection
                )
            ),
            query_embedding=FakeQueryEmbedding(),
            candidate_k=5,
        )

    def test_scope_none_uses_original_retrieval(self):
        """
        urls=None 不應加入 ChromaDB where filter。
        """

        result = self.retrieval.retrieve(
            "test query"
        )

        self.assertEqual(
            len(self.collection.calls),
            1,
        )

        call = self.collection.calls[0]

        self.assertNotIn(
            "where",
            call,
        )

        self.assertEqual(
            result["ids"],
            [["doc_1::chunk_0"]],
        )

    def test_scope_urls_adds_url_filter(self):
        """
        urls=[...] 應加入 URL $in filter。
        """

        urls = [
            "https://example.com/article",
            "https://example.com/article-2",
        ]

        result = self.retrieval.retrieve(
            "test query",
            urls=urls,
        )

        self.assertEqual(
            len(self.collection.calls),
            1,
        )

        call = self.collection.calls[0]

        self.assertEqual(
            call["where"],
            {
                "url": {
                    "$in": urls,
                }
            },
        )

        self.assertEqual(
            result["ids"],
            [["doc_1::chunk_0"]],
        )

    def test_scope_empty_returns_empty_result(self):
        """
        urls=[] 應直接回傳空結果，不執行 ChromaDB Query。
        """

        result = self.retrieval.retrieve(
            "test query",
            urls=[],
        )

        self.assertEqual(
            len(self.collection.calls),
            0,
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


class TestRAGRetrieverScope(unittest.TestCase):
    """
    測試 RAGRetriever URL Scope 傳遞。
    """

    def test_search_passes_urls_to_chroma_retrieval(self):
        """
        RAGRetriever.search() 應將 urls 傳給 ChromaDBRetrieval。
        """

        class FakeChromaRetrieval:
            def __init__(self):
                self.calls = []

            def retrieve(self, query, urls=None):
                self.calls.append(
                    {
                        "query": query,
                        "urls": urls,
                    }
                )

                return {
                    "ids": [
                        [
                            "doc_1::chunk_0",
                        ]
                    ],
                    "documents": [
                        [
                            "test document",
                        ]
                    ],
                    "metadatas": [
                        [
                            {
                                "document_id": "doc_1",
                                "url": (
                                    "https://example.com/article"
                                ),
                            }
                        ]
                    ],
                    "distances": [
                        [
                            0.1,
                        ]
                    ],
                }

        chroma_retrieval = FakeChromaRetrieval()

        retriever = RAGRetriever(
            chroma_retrieval=chroma_retrieval,
            top_k_retrieval=TopKRetrieval(
                top_k=5
            ),
            retrieval_result_builder=(
                RetrievalResultBuilder()
            ),
        )

        urls = [
            "https://example.com/article",
        ]

        results = retriever.search(
            "test query",
            urls=urls,
        )

        self.assertEqual(
            chroma_retrieval.calls,
            [
                {
                    "query": "test query",
                    "urls": urls,
                }
            ],
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].get_metadata()["url"],
            "https://example.com/article",
        )

    def test_search_without_urls_keeps_backward_compatibility(self):
        """
        不提供 urls 時仍應使用原本 search(query) API。
        """

        class FakeChromaRetrieval:
            def __init__(self):
                self.calls = []

            def retrieve(self, query, urls=None):
                self.calls.append(
                    {
                        "query": query,
                        "urls": urls,
                    }
                )

                return {
                    "ids": [
                        [
                            "doc_1::chunk_0",
                        ]
                    ],
                    "documents": [
                        [
                            "test document",
                        ]
                    ],
                    "metadatas": [
                        [
                            {
                                "document_id": "doc_1",
                                "url": (
                                    "https://example.com/article"
                                ),
                            }
                        ]
                    ],
                    "distances": [
                        [
                            0.1,
                        ]
                    ],
                }

        chroma_retrieval = FakeChromaRetrieval()

        retriever = RAGRetriever(
            chroma_retrieval=chroma_retrieval,
            top_k_retrieval=TopKRetrieval(
                top_k=5
            ),
            retrieval_result_builder=(
                RetrievalResultBuilder()
            ),
        )

        results = retriever.search(
            "test query"
        )

        self.assertEqual(
            chroma_retrieval.calls,
            [
                {
                    "query": "test query",
                    "urls": None,
                }
            ],
        )

        self.assertEqual(
            len(results),
            1,
        )


class TestRetrievalContextScope(unittest.TestCase):
    """
    測試 RetrievalContext URL Scope 傳遞。
    """

    def test_build_passes_urls_to_retriever(self):
        """
        RetrievalContext.build() 應將 urls 傳給 RAGRetriever。
        """

        retriever = FakeScopedRetriever()

        context_builder = FakeContextBuilder()

        context = RetrievalContext(
            retriever=retriever,
            context_builder=context_builder,
        )

        urls = [
            "https://example.com/article",
            "https://example.com/article-2",
        ]

        result = context.build(
            "test query",
            urls=urls,
        )

        self.assertEqual(
            retriever.calls,
            [
                {
                    "query": "test query",
                    "urls": urls,
                }
            ],
        )

        self.assertEqual(
            result,
            [],
        )

    def test_build_without_urls_keeps_all_archive_scope(self):
        """
        RetrievalContext.build(query) 應維持 urls=None。
        """

        retriever = FakeScopedRetriever()

        context = RetrievalContext(
            retriever=retriever,
            context_builder=FakeContextBuilder(),
        )

        context.build(
            "test query"
        )

        self.assertEqual(
            retriever.calls,
            [
                {
                    "query": "test query",
                    "urls": None,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()