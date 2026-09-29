"""
services/archive_chat_service.py

AutoSearch V7

R10.5

Article Archive Chat Service

用途：

    提供 Article Archive Robot 使用的
    Chat Service。

資料流程：

    Article Archive Viewer
            ↓
    ArchiveChatService
            ↓
    Snapshot History
            ↓
    Latest / Historical Snapshot
            ↓
    R10.4 Archive RAG
            ↓
    RAGQuery
            ↓
    Final Response

本 Service：

    1. 取得指定 URL 的 Snapshot History。
    2. 判斷 Latest / Historical Snapshot。
    3. 取得 Latest ChromaDB RAG Context。
    4. 取得 Historical Snapshot Difference Context。
    5. 組合 Robot Context。
    6. 沿用既有 RAGQuery。
    7. 不建立 Historical ChromaDB。
    8. 不修改 MongoDB Snapshot。
"""

from database.raw_html_repository import RawHTMLRepository
from rag.rag_query import RAGQuery


class ArchiveChatService:
    """
    R10.5 Article Archive Chat Service。

    負責：

        Article URL
            ↓
        Snapshot History
            ↓
        Latest / Historical
            ↓
        R10.4 RAG
            ↓
        Robot Response
    """

    def __init__(
        self,
        repository=None,
        rag_query=None,
    ):
        self.repository = (
            repository
            if repository is not None
            else RawHTMLRepository()
        )

        self.rag_query = (
            rag_query
            if rag_query is not None
            else RAGQuery()
        )

    def get_snapshot_history(
        self,
        url,
    ):
        """
        取得指定 URL 的所有 Snapshot History。
        """

        if not url:
            return []

        url = str(url).strip()

        if not url:
            return []

        return self.repository.find_versions_by_url(
            url
        )

    def get_snapshots(
        self,
        url,
    ):
        """
        取得指定 URL 的完整 Snapshot History。

        find_versions_by_url()
        只回傳 mongo_id 與 created_at，
        因此再依 mongo_id 取得完整 Snapshot。
        """

        versions = self.get_snapshot_history(
            url
        )

        snapshots = []

        for version in versions:
            mongo_id = version.get(
                "mongo_id"
            )

            if not mongo_id:
                continue

            snapshot = self.repository.find_by_id(
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

    def get_latest_snapshot(
        self,
        url,
    ):
        """
        取得指定 URL 的 Latest Snapshot。
        """

        snapshots = self.get_snapshots(
            url
        )

        if not snapshots:
            return None

        return snapshots[0]

    def get_historical_snapshot(
        self,
        url,
        version,
    ):
        """
        取得指定 URL 的 Historical Snapshot。

        version 可以是：

            datetime
            ISO 8601 string
        """

        if not version:
            return None

        versions = self.get_snapshot_history(
            url
        )

        normalized_version = (
            self.repository._normalize_datetime(
                version
            )
        )

        if normalized_version is None:
            return None

        for item in versions:
            created_at = item.get(
                "created_at"
            )

            normalized_created_at = (
                self.repository._normalize_datetime(
                    created_at
                )
            )

            if normalized_created_at == normalized_version:
                mongo_id = item.get(
                    "mongo_id"
                )

                if not mongo_id:
                    return None

                return self.repository.find_by_id(
                    mongo_id
                )

        return None

    def resolve_snapshots(
        self,
        url,
        version=None,
    ):
        """
        判斷 Latest / Historical Snapshot。

        沒有指定 version：

            Latest Snapshot
            Historical Snapshot = None

        指定 version：

            Latest Snapshot
            Historical Snapshot = 指定版本
        """

        latest_snapshot = self.get_latest_snapshot(
            url
        )

        if latest_snapshot is None:
            return {
                "latest": None,
                "historical": None,
            }

        if version is None:
            return {
                "latest": latest_snapshot,
                "historical": None,
            }

        historical_snapshot = (
            self.get_historical_snapshot(
                url,
                version,
            )
        )

        return {
            "latest": latest_snapshot,
            "historical": historical_snapshot,
        }

    def run(
        self,
        url,
        query,
        version=None,
    ):
        """
        執行 Article Archive Robot 問答。

        version：

            None
                ↓
            Latest Article 問答

            指定 Snapshot version
                ↓
            Latest + Historical Difference 問答
        """

        if not url:
            raise ValueError(
                "Article URL is required."
            )

        if not query:
            raise ValueError(
                "User query is required."
            )

        url = str(url).strip()
        query = str(query).strip()

        if not url:
            raise ValueError(
                "Article URL cannot be empty."
            )

        if not query:
            raise ValueError(
                "User query cannot be empty."
            )

        snapshots = self.resolve_snapshots(
            url=url,
            version=version,
        )

        latest_snapshot = snapshots.get(
            "latest"
        )

        historical_snapshot = snapshots.get(
            "historical"
        )

        if latest_snapshot is None:
            return {
                "answer": "",
                "sources": [],
            }

        return self.rag_query.run(
            query=query,
            urls=[
                url
            ],
            historical_snapshot=(
                historical_snapshot
            ),
            latest_snapshot=(
                latest_snapshot
            ),
        )


__all__ = [
    "ArchiveChatService",
]