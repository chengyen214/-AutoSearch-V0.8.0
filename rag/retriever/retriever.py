"""
rag/retriever/retriever.py

AutoSearch V7

RAG-5 Retriever Integration
"""

from rag.chroma.client import (
    ChromaDBClient,
)

from rag.chroma.collection import (
    ChromaCollection,
)

from rag.retriever.config import (
    CANDIDATE_K,
    TOP_K,
)

from rag.retriever.query_embedding import (
    QueryEmbedding,
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


class RAGRetriever:
    """
    RAG-5 統整使用入口。

    將 RAG-5.2～RAG-5.5 串接成單一 Retrieval API。
    """

    def __init__(
        self,
        chroma_client=None,
        chroma_collection=None,
        query_embedding=None,
        chroma_retrieval=None,
        top_k_retrieval=None,
        retrieval_result_builder=None,
        candidate_k=None,
        top_k=None,
    ):
        """
        初始化 RAG-5 Retriever。

        Parameters
        ----------
        chroma_client:
            可注入 ChromaDBClient。

        chroma_collection:
            可注入 ChromaCollection。

        query_embedding:
            可注入 QueryEmbedding。

        chroma_retrieval:
            可注入 ChromaDBRetrieval。

        top_k_retrieval:
            可注入 TopKRetrieval。

        retrieval_result_builder:
            可注入 RetrievalResultBuilder。

        candidate_k:
            Candidate Retrieval 數量。

        top_k:
            最終 Retrieval 結果數量。
        """

        if candidate_k is None:
            candidate_k = CANDIDATE_K

        if top_k is None:
            top_k = TOP_K

        if chroma_client is None:
            chroma_client = ChromaDBClient()

        self.chroma_client = chroma_client

        if chroma_collection is None:
            chroma_collection = ChromaCollection(
                chroma_client=self.chroma_client
            )

        self.chroma_collection = chroma_collection

        if query_embedding is None:
            query_embedding = QueryEmbedding()

        self.query_embedding = query_embedding

        if chroma_retrieval is None:
            chroma_retrieval = ChromaDBRetrieval(
                chroma_collection=self.chroma_collection,
                query_embedding=self.query_embedding,
                candidate_k=candidate_k,
            )

        self.chroma_retrieval = chroma_retrieval

        if top_k_retrieval is None:
            top_k_retrieval = TopKRetrieval(
                top_k=top_k
            )

        self.top_k_retrieval = top_k_retrieval

        if retrieval_result_builder is None:
            retrieval_result_builder = RetrievalResultBuilder()

        self.retrieval_result_builder = retrieval_result_builder

    def search(
        self,
        query,
        urls=None,
    ):
        """
        執行完整 RAG-5 Retrieval。

        urls=None:
            不限制 Archive 範圍。

        urls=[...]:
            僅檢索指定 URL。

        urls=[]:
            不取得任何 Retrieval Result。
        """

        candidate_result = (
            self.chroma_retrieval.retrieve(
                query,
                urls=urls,
            )
        )

        final_result = (
            self.top_k_retrieval.select(
                candidate_result
            )
        )

        retrieval_results = (
            self.retrieval_result_builder.build(
                final_result
            )
        )

        return retrieval_results

    def get_candidate_k(
        self
    ):
        """
        取得 Candidate-K。
        """

        return (
            self.chroma_retrieval.get_candidate_k()
        )

    def get_top_k(
        self
    ):
        """
        取得 Final Top-K。
        """

        return (
            self.top_k_retrieval.get_top_k()
        )

    def get_query_embedding(
        self
    ):
        """
        取得 QueryEmbedding。
        """

        return self.query_embedding

    def get_chroma_retrieval(
        self
    ):
        """
        取得 ChromaDBRetrieval。
        """

        return self.chroma_retrieval

    def get_top_k_retrieval(
        self
    ):
        """
        取得 TopKRetrieval。
        """

        return self.top_k_retrieval

    def get_retrieval_result_builder(
        self
    ):
        """
        取得 RetrievalResultBuilder。
        """

        return self.retrieval_result_builder


__all__ = [
    "RAGRetriever",
]