"""
tests/V8_0/test_rag_query.py

AutoSearch V7

R10.4

RAG Query Test
"""

from datetime import datetime, timezone

from rag.rag_query import RAGQuery
from rag.snapshot_document import SnapshotDocument


class MockArchiveRAGContext:
    def __init__(self):
        self.calls = []

    def build(
        self,
        query,
        urls=None,
        historical_snapshot=None,
        latest_snapshot=None,
    ):
        self.calls.append(
            {
                "query": query,
                "urls": urls,
                "historical_snapshot": historical_snapshot,
                "latest_snapshot": latest_snapshot,
            }
        )

        return {
            "entries": [
                {
                    "source_index": 1,
                    "document_id": "doc-1",
                    "chunk_index": 0,
                    "title": "Test Article",
                    "url": "https://example.com/article",
                    "content": "Latest article content",
                }
            ],
            "context_text": "Latest article content",
            "count": 1,
        }


class MockPromptBuilder:
    def __init__(self):
        self.calls = []

    def build(
        self,
        query,
        context,
    ):
        self.calls.append(
            {
                "query": query,
                "context": context,
            }
        )

        return "TEST PROMPT"


class MockLLMInvoker:
    def __init__(self):
        self.calls = []

    def invoke(
        self,
        prompt,
    ):
        self.calls.append(prompt)

        return "Test answer [Source 1]"


class MockAnswerGenerator:
    def __init__(self):
        self.calls = []

    def generate(
        self,
        llm_response,
        context,
    ):
        self.calls.append(
            {
                "llm_response": llm_response,
                "context": context,
            }
        )

        return {
            "answer_text": "Test answer",
            "source_references": [
                {
                    "source_index": 1,
                    "document_id": "doc-1",
                    "chunk_index": 0,
                    "title": "Test Article",
                    "url": "https://example.com/article",
                }
            ],
        }


class MockResponseFormatter:
    def __init__(self):
        self.calls = []

    def format(
        self,
        result,
    ):
        self.calls.append(result)

        return {
            "answer": result["answer_text"],
            "sources": result["source_references"],
        }


def create_snapshot(
    content,
    created_at,
):
    return SnapshotDocument(
        title="Test Article",
        content=content,
        url="https://example.com/article",
        snapshot_created_at=created_at,
    )


def create_rag_query():
    rag_query = RAGQuery()

    rag_query.archive_rag_context = (
        MockArchiveRAGContext()
    )

    rag_query.prompt_builder = (
        MockPromptBuilder()
    )

    rag_query.llm_invoker = (
        MockLLMInvoker()
    )

    rag_query.answer_generator = (
        MockAnswerGenerator()
    )

    rag_query.response_formatter = (
        MockResponseFormatter()
    )

    return rag_query


def test_run_with_urls():
    rag_query = create_rag_query()

    response = rag_query.run(
        query="Test query",
        urls=["https://example.com/article"],
    )

    assert response == {
        "answer": "Test answer",
        "sources": [
            {
                "source_index": 1,
                "document_id": "doc-1",
                "chunk_index": 0,
                "title": "Test Article",
                "url": "https://example.com/article",
            }
        ],
    }

    assert len(
        rag_query.archive_rag_context.calls
    ) == 1

    call = (
        rag_query.archive_rag_context.calls[0]
    )

    assert call["query"] == "Test query"
    assert call["urls"] == [
        "https://example.com/article"
    ]
    assert (
        call["historical_snapshot"]
        is None
    )
    assert (
        call["latest_snapshot"]
        is None
    )


def test_run_without_urls():
    rag_query = create_rag_query()

    response = rag_query.run(
        query="Test query",
    )

    assert response["answer"] == "Test answer"

    call = (
        rag_query.archive_rag_context.calls[0]
    )

    assert call["query"] == "Test query"
    assert call["urls"] is None
    assert (
        call["historical_snapshot"]
        is None
    )
    assert (
        call["latest_snapshot"]
        is None
    )


def test_empty_urls_returns_empty_response():
    rag_query = create_rag_query()

    response = rag_query.run(
        query="Test query",
        urls=[],
    )

    assert response == {
        "answer": "",
        "sources": [],
    }

    assert (
        rag_query.archive_rag_context.calls
        == []
    )


def test_historical_and_latest_snapshots_are_passed():
    rag_query = create_rag_query()

    historical = create_snapshot(
        "Old article content",
        datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = create_snapshot(
        "New article content",
        datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    response = rag_query.run(
        query="What changed?",
        urls=["https://example.com/article"],
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert response["answer"] == "Test answer"

    call = (
        rag_query.archive_rag_context.calls[0]
    )

    assert call["query"] == "What changed?"

    assert call["urls"] == [
        "https://example.com/article"
    ]

    assert (
        call["historical_snapshot"]
        is historical
    )

    assert (
        call["latest_snapshot"]
        is latest
    )


def test_archive_context_flows_to_prompt_builder():
    rag_query = create_rag_query()

    rag_query.run(
        query="Test query",
        urls=["https://example.com/article"],
    )

    call = (
        rag_query.prompt_builder.calls[0]
    )

    assert call["query"] == "Test query"

    assert (
        call["context"]["context_text"]
        == "Latest article content"
    )

    assert (
        call["context"]["count"]
        == 1
    )


def test_prompt_flows_to_llm_invoker():
    rag_query = create_rag_query()

    rag_query.run(
        query="Test query",
        urls=["https://example.com/article"],
    )

    assert (
        rag_query.llm_invoker.calls
        == ["TEST PROMPT"]
    )


def test_llm_response_flows_to_answer_generator():
    rag_query = create_rag_query()

    rag_query.run(
        query="Test query",
        urls=["https://example.com/article"],
    )

    call = (
        rag_query.answer_generator.calls[0]
    )

    assert (
        call["llm_response"]
        == "Test answer [Source 1]"
    )

    assert (
        call["context"]["context_text"]
        == "Latest article content"
    )


def test_answer_flows_to_response_formatter():
    rag_query = create_rag_query()

    response = rag_query.run(
        query="Test query",
        urls=["https://example.com/article"],
    )

    assert len(
        rag_query.response_formatter.calls
    ) == 1

    result = (
        rag_query.response_formatter.calls[0]
    )

    assert result == {
        "answer_text": "Test answer",
        "source_references": [
            {
                "source_index": 1,
                "document_id": "doc-1",
                "chunk_index": 0,
                "title": "Test Article",
                "url": "https://example.com/article",
            }
        ],
    }

    assert response == {
        "answer": "Test answer",
        "sources": [
            {
                "source_index": 1,
                "document_id": "doc-1",
                "chunk_index": 0,
                "title": "Test Article",
                "url": "https://example.com/article",
            }
        ],
    }


def test_full_r10_4_flow_passes_snapshots_through_context_layer():
    rag_query = create_rag_query()

    historical = create_snapshot(
        "Old content",
        datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = create_snapshot(
        "New content",
        datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    rag_query.run(
        query="Compare versions",
        urls=["https://example.com/article"],
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    archive_call = (
        rag_query.archive_rag_context.calls[0]
    )

    prompt_call = (
        rag_query.prompt_builder.calls[0]
    )

    llm_call = (
        rag_query.llm_invoker.calls[0]
    )

    answer_call = (
        rag_query.answer_generator.calls[0]
    )

    formatter_call = (
        rag_query.response_formatter.calls[0]
    )

    assert (
        archive_call["historical_snapshot"]
        is historical
    )

    assert (
        archive_call["latest_snapshot"]
        is latest
    )

    assert (
        prompt_call["context"]
        is answer_call["context"]
    )

    assert llm_call == "TEST PROMPT"

    assert (
        answer_call["llm_response"]
        == "Test answer [Source 1]"
    )

    assert formatter_call["answer_text"] == (
        "Test answer"
    )