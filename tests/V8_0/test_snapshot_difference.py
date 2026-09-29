"""
tests/V8_0/test_snapshot_difference.py

AutoSearch V7

R10.3

Snapshot Difference Test
"""

from datetime import datetime, timezone

import pytest

from rag.snapshot_difference import (
    SnapshotDifference,
)
from rag.snapshot_document import (
    SnapshotDocument,
)


def create_snapshot(
    content,
    url="https://example.com/article",
):
    return SnapshotDocument(
        title="Test Article",
        content=content,
        url=url,
        snapshot_created_at=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )


def test_added_content():
    historical = create_snapshot(
        "A\nB\nC"
    )

    latest = create_snapshot(
        "A\nB\nC\nD"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == ["D"]
    assert difference.deleted == []
    assert difference.modified == []
    assert difference.has_changes is True


def test_deleted_content():
    historical = create_snapshot(
        "A\nB\nC"
    )

    latest = create_snapshot(
        "A\nC"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == []
    assert difference.deleted == ["B"]
    assert difference.modified == []
    assert difference.has_changes is True


def test_modified_content():
    historical = create_snapshot(
        "A\nOld content\nC"
    )

    latest = create_snapshot(
        "A\nNew content\nC"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == []
    assert difference.deleted == []
    assert difference.modified == [
        {
            "historical": ["Old content"],
            "latest": ["New content"],
        }
    ]
    assert difference.has_changes is True


def test_added_and_deleted_content():
    historical = create_snapshot(
        "A\nOld\nC"
    )

    latest = create_snapshot(
        "A\nC\nNew"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.deleted == ["Old"]
    assert difference.added == ["New"]
    assert difference.modified == []
    assert difference.has_changes is True


def test_multiple_modified_lines():
    historical = create_snapshot(
        "A\nOld A\nOld B\nD"
    )

    latest = create_snapshot(
        "A\nNew A\nNew B\nD"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == []
    assert difference.deleted == []
    assert difference.modified == [
        {
            "historical": [
                "Old A",
                "Old B",
            ],
            "latest": [
                "New A",
                "New B",
            ],
        }
    ]


def test_no_changes():
    historical = create_snapshot(
        "A\nB\nC"
    )

    latest = create_snapshot(
        "A\nB\nC"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == []
    assert difference.deleted == []
    assert difference.modified == []
    assert difference.has_changes is False


def test_empty_content():
    historical = create_snapshot(
        ""
    )

    latest = create_snapshot(
        "New content"
    )

    difference = SnapshotDifference.compare(
        historical,
        latest,
    )

    assert difference.added == ["New content"]
    assert difference.deleted == []
    assert difference.modified == []


def test_urls_must_match():
    historical = create_snapshot(
        "A",
        url="https://example.com/old",
    )

    latest = create_snapshot(
        "A",
        url="https://example.com/new",
    )

    with pytest.raises(
        ValueError,
        match="URLs must match",
    ):
        SnapshotDifference.compare(
            historical,
            latest,
        )


def test_historical_cannot_be_none():
    latest = create_snapshot(
        "A"
    )

    with pytest.raises(
        ValueError,
        match="Historical SnapshotDocument cannot be None",
    ):
        SnapshotDifference.compare(
            None,
            latest,
        )


def test_latest_cannot_be_none():
    historical = create_snapshot(
        "A"
    )

    with pytest.raises(
        ValueError,
        match="Latest SnapshotDocument cannot be None",
    ):
        SnapshotDifference.compare(
            historical,
            None,
        )


def test_historical_must_be_snapshot_document():
    latest = create_snapshot(
        "A"
    )

    with pytest.raises(
        TypeError,
        match="Historical must be a SnapshotDocument",
    ):
        SnapshotDifference.compare(
            {},
            latest,
        )


def test_latest_must_be_snapshot_document():
    historical = create_snapshot(
        "A"
    )

    with pytest.raises(
        TypeError,
        match="Latest must be a SnapshotDocument",
    ):
        SnapshotDifference.compare(
            historical,
            {},
        )


def test_snapshot_documents_are_not_modified():
    historical = create_snapshot(
        "A\nOld\nC"
    )

    latest = create_snapshot(
        "A\nNew\nC"
    )

    historical_content = historical.content
    latest_content = latest.content

    SnapshotDifference.compare(
        historical,
        latest,
    )

    assert historical.content == historical_content
    assert latest.content == latest_content