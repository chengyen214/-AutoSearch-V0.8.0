"""
rag/rag_query.py

AutoSearch V7

RAG Query Entry

流程:
    User Query
        ↓
    RAG-5 Retriever
        ↓
    RAG-6 Context Builder
        ↓
    R10.4 Archive RAG Context
        ↓
    RAG-7.2 Prompt Construction
        ↓
    RAG-7.4 LLM Invocation
        ↓
    RAG-7.5 Answer Generation
        ↓
    RAG-8 Response Formatting
        ↓
    Final Response

用途:
    提供單一入口，串聯 RAG-5 至 RAG-8
    與 R10.4 Latest + Historical RAG。
"""

from rag.retrieval_context import RetrievalContext
from rag.archive_rag_context import ArchiveRAGContext
from rag.generation.prompt_builder import PromptBuilder
from rag.generation.llm_invoker import LLMInvoker
from rag.generation.answer_generator import AnswerGenerator
from rag.response_formatter import ResponseFormatter


class RAGQuery:
    def __init__(self):
        self.retrieval_context = RetrievalContext()
        self.archive_rag_context = ArchiveRAGContext(
            retrieval_context=self.retrieval_context
        )
        self.prompt_builder = PromptBuilder()
        self.llm_invoker = LLMInvoker()
        self.answer_generator = AnswerGenerator()
        self.response_formatter = ResponseFormatter()

    def run(
        self,
        query: str,
        urls=None,
        historical_snapshot=None,
        latest_snapshot=None,
    ):
        if urls == []:
            return {
                "answer": "",
                "sources": [],
            }

        context = self.archive_rag_context.build(
            query=query,
            urls=urls,
            historical_snapshot=historical_snapshot,
            latest_snapshot=latest_snapshot,
        )

        prompt = self.prompt_builder.build(
            query=query,
            context=context,
        )

        llm_response = self.llm_invoker.invoke(
            prompt
        )

        result = self.answer_generator.generate(
            llm_response=llm_response,
            context=context,
        )

        response = self.response_formatter.format(
            result
        )

        return response