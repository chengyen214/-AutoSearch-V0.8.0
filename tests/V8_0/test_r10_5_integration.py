"""
tests/V8_0/test_r10_5_integration.py

AutoSearch V7

R10.5

Article Archive Chat API
Real Integration Test

驗證：

    Article Archive Viewer
            ↓
    POST /archive/chat
            ↓
    ArchiveChatService
            ↓
    MongoDB Snapshot History
            ↓
    R10.4 Archive RAG
            ↓
    ChromaDB
            ↓
    Embedding
            ↓
    Groq
            ↓
    Final Response

本測試：

    1. 不使用 Mock。
    2. 使用真實 FastAPI。
    3. 使用真實 MongoDB。
    4. 使用真實 ChromaDB。
    5. 使用真實 Embedding。
    6. 使用真實 Groq。
    7. 不修改 MongoDB Snapshot。
"""

from fastapi.testclient import TestClient

from api.main import app
from database.raw_html_repository import RawHTMLRepository


client = TestClient(app)


def _get_snapshot_history(
    repository,
    url,
):
    """
    取得指定 URL 的完整 Snapshot History。
    """

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


def _find_test_url(
    repository,
):
    """
    尋找至少具有兩個 Snapshot 的真實 URL。
    """

    collection = repository.collection

    urls = collection.distinct(
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


def test_r10_5_real_latest_chat_integration():
    """
    R10.5 Latest Article Chat Real Integration。
    """

    repository = RawHTMLRepository()

    url, snapshots, checked_urls = (
        _find_test_url(
            repository
        )
    )

    assert url is not None
    assert len(snapshots) >= 2

    response = client.post(
        "/archive/chat",
        json={
            "url": url,
            "query": "請整理這篇文章的主要內容。",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        dict,
    )

    assert "answer" in data
    assert "sources" in data

    assert isinstance(
        data["answer"],
        str,
    )

    assert data["answer"].strip()

    assert isinstance(
        data["sources"],
        list,
    )

    print()
    print("R10.5 Latest Chat Integration")
    print("=" * 60)
    print(
        f"Checked URLs              : "
        f"{checked_urls}"
    )
    print(
        f"Selected URL              : "
        f"{url}"
    )
    print(
        f"Snapshot Count             : "
        f"{len(snapshots)}"
    )
    print(
        f"Latest Snapshot            : "
        f"{snapshots[0].get('created_at')}"
    )
    print(
        f"HTTP Status                : "
        f"{response.status_code}"
    )
    print(
        f"Answer Length              : "
        f"{len(data['answer'])}"
    )
    print(
        f"Sources                    : "
        f"{len(data['sources'])}"
    )
    print()
    print("R10.5 Latest Chat Integration: PASS")


def test_r10_5_real_historical_chat_integration():
    """
    R10.5 Historical Snapshot Chat Real Integration。
    """

    repository = RawHTMLRepository()

    url, snapshots, checked_urls = (
        _find_test_url(
            repository
        )
    )

    assert url is not None
    assert len(snapshots) >= 2

    latest_snapshot = snapshots[0]
    historical_snapshot = snapshots[1]

    version = historical_snapshot.get(
        "created_at"
    )

    assert version is not None

    if hasattr(
        version,
        "isoformat",
    ):
        version = version.isoformat()

    response = client.post(
        "/archive/chat",
        json={
            "url": url,
            "query": (
                "請比較這個歷史版本與最新版本的內容差異。"
            ),
            "version": version,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        dict,
    )

    assert "answer" in data
    assert "sources" in data

    assert isinstance(
        data["answer"],
        str,
    )

    assert data["answer"].strip()

    assert isinstance(
        data["sources"],
        list,
    )

    print()
    print("R10.5 Historical Chat Integration")
    print("=" * 60)
    print(
        f"Checked URLs              : "
        f"{checked_urls}"
    )
    print(
        f"Selected URL              : "
        f"{url}"
    )
    print(
        f"Historical Snapshot        : "
        f"{historical_snapshot.get('created_at')}"
    )
    print(
        f"Latest Snapshot            : "
        f"{latest_snapshot.get('created_at')}"
    )
    print(
        f"HTTP Status                : "
        f"{response.status_code}"
    )
    print(
        f"Answer Length              : "
        f"{len(data['answer'])}"
    )
    print(
        f"Sources                    : "
        f"{len(data['sources'])}"
    )
    print()
    print(
        "R10.5 Historical Chat "
        "Integration: PASS"
    )