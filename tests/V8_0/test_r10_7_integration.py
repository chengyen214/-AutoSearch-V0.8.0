"""
tests/V8_0/test_r10_7_integration.py

AutoSearch V7

R10.7

Article Archive Chatbot End-to-End Integration Test

驗證：

    Article Archive Viewer
            ↓
    /archive/chat
            ↓
    ArchiveChatService
            ↓
    MongoDB Snapshot
            ↓
    R10.4 Archive RAG
            ↓
    ChromaDB
            ↓
    Embedding
            ↓
    Groq
            ↓
    Robot Answer

本測試：

    1. 使用真實 FastAPI App。
    2. 使用真實 MongoDB。
    3. 使用真實 Snapshot。
    4. 使用真實 ChromaDB。
    5. 使用真實 Embedding。
    6. 使用真實 Groq。
    7. 不使用 Mock。
    8. 驗證 Latest 問答。
    9. 驗證 Historical 問答。
    10. 驗證 Archive Viewer 頁面存在 Robot UI。
"""

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from api.main import app
from database.raw_html_repository import RawHTMLRepository


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "archive"
    / "viewer.html"
)


def _get_snapshot_history(
    repository,
    url,
):
    versions = repository.find_versions_by_url(
        url
    )

    snapshots = []

    for version in versions:

        mongo_id = version.get(
            "mongo_id"
        )

        if not mongo_id:
            continue

        snapshot = repository.find_by_id(
            mongo_id
        )

        if snapshot is None:
            continue

        snapshots.append(
            snapshot
        )

    snapshots.sort(
        key=lambda snapshot: (
            snapshot.get(
                "created_at"
            )
        ),
        reverse=True,
    )

    return snapshots


def _find_url_with_snapshots(
    repository,
):
    urls = repository.collection.distinct(
        "url"
    )

    checked_urls = 0

    for url in urls:

        if not url:
            continue

        checked_urls += 1

        snapshots = _get_snapshot_history(
            repository,
            url,
        )

        if len(snapshots) >= 2:

            return (
                url,
                snapshots,
                checked_urls,
            )

    return (
        None,
        [],
        checked_urls,
    )


def test_r10_7_archive_viewer_and_chat_e2e():
    """
    驗證 Article Archive Viewer
    與 Archive Robot 的完整整合流程。
    """

    if not TEMPLATE_PATH.exists():
        pytest.fail(
            "viewer.html does not exist."
        )

    html = TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        'class="archive-chat"'
        in html
    )

    assert (
        "Article Archive Robot"
        in html
    )

    assert (
        'fetch('
        in html
    )

    assert (
        '"/archive/chat"'
        in html
    )

    repository = RawHTMLRepository()

    (
        url,
        snapshots,
        checked_urls,
    ) = _find_url_with_snapshots(
        repository
    )

    print()
    print(
        "R10.7 Article Archive Chatbot "
        "End-to-End Integration"
    )
    print(
        "=" * 60
    )
    print(
        f"Checked URLs       : "
        f"{checked_urls}"
    )

    if not url:

        print(
            "No URL with >= 2 Snapshots found."
        )

        pytest.skip(
            "No URL with at least two snapshots."
        )

    latest_snapshot = snapshots[0]
    historical_snapshot = snapshots[1]

    print(
        f"Selected URL       : "
        f"{url}"
    )

    print(
        f"Snapshot Count     : "
        f"{len(snapshots)}"
    )

    print(
        f"Historical Snapshot: "
        f"{historical_snapshot.get('created_at')}"
    )

    print(
        f"Latest Snapshot    : "
        f"{latest_snapshot.get('created_at')}"
    )

    client = TestClient(
        app
    )

    print()
    print(
        "Step 1: Archive Viewer"
    )

    viewer_response = client.get(
        "/archive/view",
        params={
            "url": url,
        },
    )

    print(
        f"HTTP Status         : "
        f"{viewer_response.status_code}"
    )

    assert (
        viewer_response.status_code
        == 200
    )

    viewer_html = (
        viewer_response.text
    )

    assert (
        "Article Archive Robot"
        in viewer_html
    )

    assert (
        'id="archive-chat-input"'
        in viewer_html
    )

    assert (
        'id="archive-chat-send"'
        in viewer_html
    )

    assert (
        '"/archive/chat"'
        in viewer_html
    )

    print(
        "Archive Viewer UI   : PASS"
    )

    print()
    print(
        "Step 2: Latest Robot Chat"
    )

    latest_query = (
        "請整理這篇文章的主要內容。"
    )

    latest_response = client.post(
        "/archive/chat",
        json={
            "url": url,
            "query": latest_query,
            "version": None,
        },
    )

    print(
        f"HTTP Status         : "
        f"{latest_response.status_code}"
    )

    assert (
        latest_response.status_code
        == 200
    )

    latest_data = (
        latest_response.json()
    )

    latest_answer = (
        latest_data.get(
            "answer",
            ""
        )
    )

    latest_sources = (
        latest_data.get(
            "sources",
            []
        )
    )

    assert isinstance(
        latest_answer,
        str,
    )

    assert latest_answer.strip()

    assert isinstance(
        latest_sources,
        list,
    )

    print(
        f"Answer Length       : "
        f"{len(latest_answer)}"
    )

    print(
        f"Sources             : "
        f"{len(latest_sources)}"
    )

    print(
        "Latest Robot Chat   : PASS"
    )

    print()
    print(
        "Step 3: Historical Robot Chat"
    )

    historical_version = (
        historical_snapshot.get(
            "created_at"
        )
    )

    assert (
        historical_version
        is not None
    )

    historical_query = (
        "請比較這個歷史版本與最新版本的內容差異。"
    )

    historical_response = client.post(
        "/archive/chat",
        json={
            "url": url,
            "query": historical_query,
            "version": (
                historical_version.isoformat()
            ),
        },
    )

    print(
        f"HTTP Status         : "
        f"{historical_response.status_code}"
    )

    assert (
        historical_response.status_code
        == 200
    )

    historical_data = (
        historical_response.json()
    )

    historical_answer = (
        historical_data.get(
            "answer",
            ""
        )
    )

    historical_sources = (
        historical_data.get(
            "sources",
            []
        )
    )

    assert isinstance(
        historical_answer,
        str,
    )

    assert historical_answer.strip()

    assert isinstance(
        historical_sources,
        list,
    )

    print(
        f"Answer Length       : "
        f"{len(historical_answer)}"
    )

    print(
        f"Sources             : "
        f"{len(historical_sources)}"
    )

    print(
        "Historical Robot    : PASS"
    )

    print()
    print(
        "R10.7 End-to-End Integration: PASS"
    )


__all__ = [
    "test_r10_7_archive_viewer_and_chat_e2e",
]