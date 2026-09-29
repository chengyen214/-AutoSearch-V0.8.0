"""
rag/snapshot_document.py

AutoSearch V7

R10.2

Snapshot Content Extraction

用途：

    將 MongoDB Snapshot 的 HTML
    轉換為可供 RAG 使用的 Document。

資料流程：

    MongoDB Snapshot
          ↓
    Snapshot HTML
          ↓
    Parser
          ↓
    ContentCleaner
          ↓
    SnapshotDocument
          ↓
    R10.3 Snapshot Version Mapping

保留資訊：

    - Article title
    - Article content
    - URL
    - Snapshot created_at

本模組：

    1. 不修改 MongoDB Snapshot。
    2. 不重新 Crawl。
    3. 沿用既有 Parser。
    4. 沿用既有 ContentCleaner。
    5. 不執行 Chunking。
    6. 不執行 Embedding。
    7. 不使用 ChromaDB。
    8. 不執行 LLM。
"""

from dataclasses import dataclass
from datetime import datetime

from parser.parser import parse
from rag.content_cleaner import ContentCleaner


@dataclass
class SnapshotDocument:
    """
    R10.2 Snapshot Document。

    保存單一 Snapshot 的文章內容與版本資訊。
    """

    title: str
    content: str
    url: str
    snapshot_created_at: datetime

    @classmethod
    def from_snapshot(
        cls,
        snapshot,
    ):
        """
        將 MongoDB Snapshot 轉換為 SnapshotDocument。
        """

        if snapshot is None:
            raise ValueError(
                "Snapshot cannot be None."
            )

        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "Snapshot must be a dict."
            )

        html = snapshot.get(
            "html"
        )

        if html is None:
            raise ValueError(
                "Snapshot requires html."
            )

        if isinstance(
            html,
            str,
        ):
            if not html.strip():
                raise ValueError(
                    "Snapshot html cannot be empty."
                )
        elif not isinstance(
            html,
            bytes,
        ):
            raise TypeError(
                "Snapshot html must be str or bytes."
            )

        url = str(
            snapshot.get(
                "url",
                ""
            )
        ).strip()

        if not url:
            raise ValueError(
                "Snapshot requires url."
            )

        snapshot_created_at = snapshot.get(
            "created_at"
        )

        if snapshot_created_at is None:
            raise ValueError(
                "Snapshot requires created_at."
            )

        article = parse(
            html,
            keyword=url,
            url=url,
        )

        content = ContentCleaner.clean(
            article.content
        )

        title = getattr(
            article,
            "title",
            ""
        )

        if title is None:
            title = ""

        title = str(
            title
        ).strip()

        return cls(
            title=title,
            content=content,
            url=url,
            snapshot_created_at=snapshot_created_at,
        )


__all__ = [
    "SnapshotDocument",
]