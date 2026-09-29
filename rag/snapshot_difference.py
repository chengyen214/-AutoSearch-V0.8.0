"""
rag/snapshot_difference.py

AutoSearch V7

R10.3

Snapshot HTML Difference

用途：

    比較 Historical Snapshot 與 Latest Snapshot
    的清理後文章內容。

資料流程：

    Historical Snapshot
          ↓
    SnapshotDocument
          ↓
    Historical Content
          ↓
                         SnapshotDifference
          ↑
    Latest Content
          ↑
    SnapshotDocument
          ↑
    Latest Snapshot

差異類型：

    - added
    - deleted
    - modified

本模組：

    1. 不修改 MongoDB Snapshot。
    2. 不修改 SnapshotDocument。
    3. 不重新 Crawl。
    4. 不使用 ChromaDB。
    5. 不執行 Embedding。
    6. 不執行 LLM。
"""

from dataclasses import dataclass
from difflib import SequenceMatcher

from rag.snapshot_document import SnapshotDocument


@dataclass
class SnapshotDifference:
    """
    R10.3 Snapshot Content Difference。

    保存 Historical Snapshot 與 Latest Snapshot
    之間的內容差異。
    """

    added: list[str]
    deleted: list[str]
    modified: list[dict]

    @property
    def has_changes(self):
        """
        判斷 Snapshot 是否存在內容差異。
        """

        return bool(
            self.added
            or self.deleted
            or self.modified
        )

    @classmethod
    def compare(
        cls,
        historical,
        latest,
    ):
        """
        比較 Historical Snapshot 與 Latest Snapshot。

        Parameters:
            historical:
                Historical SnapshotDocument。

            latest:
                Latest SnapshotDocument。

        Returns:
            SnapshotDifference
        """

        if historical is None:
            raise ValueError(
                "Historical SnapshotDocument cannot be None."
            )

        if latest is None:
            raise ValueError(
                "Latest SnapshotDocument cannot be None."
            )

        if not isinstance(
            historical,
            SnapshotDocument,
        ):
            raise TypeError(
                "Historical must be a SnapshotDocument."
            )

        if not isinstance(
            latest,
            SnapshotDocument,
        ):
            raise TypeError(
                "Latest must be a SnapshotDocument."
            )

        if historical.url != latest.url:
            raise ValueError(
                "Historical and Latest URLs must match."
            )

        historical_lines = historical.content.splitlines()
        latest_lines = latest.content.splitlines()

        matcher = SequenceMatcher(
            None,
            historical_lines,
            latest_lines,
        )

        added = []
        deleted = []
        modified = []

        for tag, historical_start, historical_end, latest_start, latest_end in (
            matcher.get_opcodes()
        ):
            if tag == "insert":
                added.extend(
                    latest_lines[
                        latest_start:latest_end
                    ]
                )

            elif tag == "delete":
                deleted.extend(
                    historical_lines[
                        historical_start:historical_end
                    ]
                )

            elif tag == "replace":
                modified.append(
                    {
                        "historical": historical_lines[
                            historical_start:historical_end
                        ],
                        "latest": latest_lines[
                            latest_start:latest_end
                        ],
                    }
                )

        return cls(
            added=added,
            deleted=deleted,
            modified=modified,
        )


__all__ = [
    "SnapshotDifference",
]