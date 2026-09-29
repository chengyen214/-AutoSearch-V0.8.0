"""
rag/retrieval_context.py

AutoSearch V7

RAG-5 → RAG-6 Integration
"""

from rag.retriever.retriever import (
    RAGRetriever,
)

from rag.context.context_builder import (
    ContextBuilder,
)


class RetrievalContext:
    """
    RAG-5 → RAG-6 整合入口。

    負責將 User Query、RAG-5 RetrievalResult
    與 RAG-6 Context 串接成單一 API。
    """

    def __init__(
        self,
        retriever=None,
        context_builder=None,
    ):
        """
        初始化 RAG-5 → RAG-6 整合入口。

        Parameters
        ----------
        retriever:
            可注入 RAGRetriever。

        context_builder:
            可注入 ContextBuilder。
        """

        if retriever is None:
            retriever = RAGRetriever()

        self.retriever = retriever

        if context_builder is None:
            context_builder = ContextBuilder()

        self.context_builder = context_builder

    def build(
        self,
        query,
        urls=None,
    ):
        """
        執行完整 RAG-5 → RAG-6 流程。

        urls=None:
            不限制 Archive 範圍。

        urls=[...]:
            僅檢索指定 URL。

        urls=[]:
            不取得任何 Retrieval Result。
        """

        retrieval_results = (
            self.retriever.search(
                query,
                urls=urls,
            )
        )

        context = (
            self.context_builder.build(
                retrieval_results
            )
        )

        return context

    def get_retriever(
        self,
    ):
        """
        取得 RAG-5 Retriever。
        """

        return self.retriever

    def get_context_builder(
        self,
    ):
        """
        取得 RAG-6 ContextBuilder。
        """

        return self.context_builder


__all__ = [
    "RetrievalContext",
]