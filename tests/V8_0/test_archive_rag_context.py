"""
tests/V8_0/test_archive_rag_context.py

AutoSearch V7

R10.4

Archive RAG Context Test
"""

from datetime import datetime, timezone

import pytest

from rag.archive_rag_context import (
    ArchiveRAGContext,
)
from rag.retrieval_context import (
    RetrievalContext,
)
from rag.snapshot_document import (
    SnapshotDocument,
)


class MockRetrievalContext:
    def __init__(self, context=None):
        self.context = context or {
            "entries": [],
            "context_text": "Latest Article Context",
            "count": 0,
        }

    def build(self, query, urls=None):
        return self.context


def create_snapshot(
    content,
    created_at,
    url="https://example.com/article",
):
    return {
        "url": url,
        "created_at": created_at,
        "html": f"<html><body>{content}</body></html>",
    }


def test_initializes_default_retrieval_context():
    archive_context = ArchiveRAGContext()

    assert isinstance(
        archive_context.retrieval_context,
        RetrievalContext,
    )


def test_accepts_injected_retrieval_context():
    retrieval_context = MockRetrievalContext()

    archive_context = ArchiveRAGContext(
        retrieval_context=retrieval_context
    )

    assert (
        archive_context.retrieval_context
        is retrieval_context
    )


def test_build_latest_context():
    retrieval_context = MockRetrievalContext()

    archive_context = ArchiveRAGContext(
        retrieval_context=retrieval_context
    )

    context = archive_context.build_latest_context(
        query="test query",
        urls=["https://example.com/article"],
    )

    assert context["context_text"] == (
        "Latest Article Context"
    )


def test_build_difference_context():
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

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build_difference_context(
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert "Historical Snapshot Time:" in context
    assert "Latest Snapshot Time:" in context
    assert "Modified Content:" in context
    assert "Old content" in context
    assert "New content" in context


def test_build_difference_context_with_added_content():
    historical = create_snapshot(
        "A\nB",
        datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = create_snapshot(
        "A\nB\nC",
        datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build_difference_context(
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert "Added Content:" in context
    assert "C" in context


def test_build_difference_context_with_deleted_content():
    historical = create_snapshot(
        "A\nB\nC",
        datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = create_snapshot(
        "A\nB",
        datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build_difference_context(
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert "Deleted Content:" in context
    assert "C" in context


def test_build_difference_context_with_no_changes():
    historical = create_snapshot(
        "A\nB\nC",
        datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = create_snapshot(
        "A\nB\nC",
        datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build_difference_context(
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert (
        "No content differences were detected."
        in context
    )


def test_combine_latest_and_historical_context():
    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    latest_context = {
        "entries": [],
        "context_text": "Latest Context",
        "count": 0,
    }

    combined = archive_context.combine(
        latest_context=latest_context,
        historical_context="Historical Difference",
    )

    assert (
        combined["context_text"]
        == "Latest Context\n\n"
        "[Historical Snapshot Context]\n"
        "Historical Difference"
    )

    assert combined["entries"] == []
    assert combined["count"] == 0


def test_combine_without_historical_context():
    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    latest_context = {
        "entries": [],
        "context_text": "Latest Context",
        "count": 0,
    }

    combined = archive_context.combine(
        latest_context=latest_context,
        historical_context=None,
    )

    assert combined == latest_context


def test_build_without_snapshots_returns_latest_context():
    retrieval_context = MockRetrievalContext()

    archive_context = ArchiveRAGContext(
        retrieval_context=retrieval_context
    )

    context = archive_context.build(
        query="test query",
        urls=["https://example.com/article"],
    )

    assert context["context_text"] == (
        "Latest Article Context"
    )


def test_build_with_snapshots_combines_context():
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

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build(
        query="What changed?",
        urls=["https://example.com/article"],
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert (
        "Latest Article Context"
        in context["context_text"]
    )

    assert (
        "[Historical Snapshot Context]"
        in context["context_text"]
    )

    assert (
        "Old content"
        in context["context_text"]
    )

    assert (
        "New content"
        in context["context_text"]
    )


def test_snapshot_document_is_accepted():
    historical = SnapshotDocument(
        title="Article",
        content="Old content",
        url="https://example.com/article",
        snapshot_created_at=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    latest = SnapshotDocument(
        title="Article",
        content="New content",
        url="https://example.com/article",
        snapshot_created_at=datetime(
            2026,
            9,
            10,
            tzinfo=timezone.utc,
        ),
    )

    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    context = archive_context.build_difference_context(
        historical_snapshot=historical,
        latest_snapshot=latest,
    )

    assert "Old content" in context
    assert "New content" in context


def test_invalid_latest_context_type():
    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    with pytest.raises(
        TypeError,
        match="latest_context must be a dictionary",
    ):
        archive_context.combine(
            latest_context=[],
            historical_context="History",
        )


def test_latest_context_requires_context_text():
    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    with pytest.raises(
        ValueError,
        match="latest_context must contain 'context_text'",
    ):
        archive_context.combine(
            latest_context={},
            historical_context="History",
        )


def test_historical_context_must_be_string():
    archive_context = ArchiveRAGContext(
        retrieval_context=MockRetrievalContext()
    )

    latest_context = {
        "entries": [],
        "context_text": "Latest Context",
        "count": 0,
    }

    with pytest.raises(
        TypeError,
        match="historical_context must be a string",
    ):
        archive_context.combine(
            latest_context=latest_context,
            historical_context={},
        )