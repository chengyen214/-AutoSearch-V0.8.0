from datetime import datetime, timezone

import pytest

from rag.snapshot_document import SnapshotDocument


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Semiconductor Industry Report</title>
</head>
<body>
    <header>
        Site Navigation
    </header>

    <main>
        <article>
            <h1>Semiconductor Industry Report</h1>

            <p>
                The semiconductor industry continues to expand as demand
                for advanced computing, artificial intelligence,
                high performance computing, and data center applications
                increases across global markets.
            </p>

            <p>
                Manufacturers are investing in advanced process technology,
                packaging capacity, memory production, and infrastructure
                to support long term growth and increasing system complexity.
            </p>

            <p>
                Industry participants are also monitoring supply chain
                conditions, technology transitions, capital expenditure,
                and demand changes across different application markets.
            </p>
        </article>
    </main>

    <footer>
        Footer content
    </footer>
</body>
</html>
"""


def create_snapshot():
    created_at = datetime(
        2026,
        9,
        28,
        10,
        30,
        0,
        tzinfo=timezone.utc,
    )

    return {
        "_id": "snapshot-test-001",
        "url": "https://example.com/article",
        "created_at": created_at,
        "html": SAMPLE_HTML,
        "content_hash": "test-hash",
        "mime_type": "text/html",
    }


def test_from_snapshot_returns_snapshot_document():
    snapshot = create_snapshot()

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert isinstance(
        document,
        SnapshotDocument,
    )


def test_from_snapshot_preserves_title():
    snapshot = create_snapshot()

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert document.title == (
        "Semiconductor Industry Report"
    )


def test_from_snapshot_extracts_content():
    snapshot = create_snapshot()

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert document.content
    assert "semiconductor industry" in (
        document.content.lower()
    )


def test_from_snapshot_cleans_content():
    snapshot = create_snapshot()

    snapshot["html"] = """
    <html>
    <head>
        <title>Test Article</title>
    </head>
    <body>
        <article>
            <p>
                First paragraph with useful article content.
            </p>


            <p>
                Second paragraph with useful article content.
            </p>
        </article>
    </body>
    </html>
    """

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert "\r" not in document.content
    assert "\n\n\n" not in document.content
    assert document.content == document.content.strip()


def test_from_snapshot_preserves_url():
    snapshot = create_snapshot()

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert document.url == (
        "https://example.com/article"
    )


def test_from_snapshot_preserves_created_at():
    snapshot = create_snapshot()

    document = SnapshotDocument.from_snapshot(
        snapshot
    )

    assert document.snapshot_created_at == (
        snapshot["created_at"]
    )


def test_from_snapshot_requires_snapshot():
    with pytest.raises(
        ValueError,
        match="Snapshot cannot be None",
    ):
        SnapshotDocument.from_snapshot(
            None
        )


def test_from_snapshot_requires_html():
    snapshot = create_snapshot()
    snapshot.pop("html")

    with pytest.raises(
        ValueError,
        match="Snapshot requires html",
    ):
        SnapshotDocument.from_snapshot(
            snapshot
        )


def test_from_snapshot_rejects_empty_html():
    snapshot = create_snapshot()
    snapshot["html"] = "   "

    with pytest.raises(
        ValueError,
        match="Snapshot html cannot be empty",
    ):
        SnapshotDocument.from_snapshot(
            snapshot
        )


def test_from_snapshot_requires_url():
    snapshot = create_snapshot()
    snapshot["url"] = ""

    with pytest.raises(
        ValueError,
        match="Snapshot requires url",
    ):
        SnapshotDocument.from_snapshot(
            snapshot
        )


def test_from_snapshot_requires_created_at():
    snapshot = create_snapshot()
    snapshot.pop("created_at")

    with pytest.raises(
        ValueError,
        match="Snapshot requires created_at",
    ):
        SnapshotDocument.from_snapshot(
            snapshot
        )


def test_from_snapshot_does_not_modify_snapshot():
    snapshot = create_snapshot()

    original_html = snapshot["html"]
    original_url = snapshot["url"]
    original_created_at = snapshot["created_at"]

    SnapshotDocument.from_snapshot(
        snapshot
    )

    assert snapshot["html"] == original_html
    assert snapshot["url"] == original_url
    assert snapshot["created_at"] == (
        original_created_at
    )