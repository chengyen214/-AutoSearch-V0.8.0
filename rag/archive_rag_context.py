"""
rag/archive_rag_context.py

AutoSearch V7

R10.4

Archive RAG Context

用途：

    組合 Latest ChromaDB RAG Context
    與 Historical Snapshot Difference Context。

資料流程：

    Latest Article
        ↓
    RetrievalContext
        ↓
    Latest Context

    Historical Snapshot
        ↓
    SnapshotDocument
        ↓
    SnapshotDifference
        ↓
    Historical Context

    Latest Context
        +
    Historical Context
        ↓
    Combined Context
"""

from rag.retrieval_context import RetrievalContext
from rag.snapshot_document import SnapshotDocument
from rag.snapshot_difference import SnapshotDifference


class ArchiveRAGContext:
    """
    R10.4 Latest + Historical RAG Context。

    負責：

        1. 取得 Latest RAG Context
        2. 比較 Historical Snapshot 與 Latest Snapshot
        3. 建立 Historical Difference Context
        4. 組合 Latest 與 Historical Context

    不負責：

        1. Historical ChromaDB
        2. Embedding
        3. LLM
        4. Prompt Construction
    """

    def __init__(
        self,
        retrieval_context=None,
    ):
        self.retrieval_context = (
            retrieval_context
            if retrieval_context is not None
            else RetrievalContext()
        )

    def build_latest_context(
        self,
        query,
        urls=None,
    ):
        """
        取得 Latest Article 的既有 RAG Context。
        """

        return self.retrieval_context.build(
            query=query,
            urls=urls,
        )

    def build_difference_context(
        self,
        historical_snapshot,
        latest_snapshot,
    ):
        """
        建立 Historical Snapshot Difference Context。
        """

        historical_document = self._to_snapshot_document(
            historical_snapshot
        )

        latest_document = self._to_snapshot_document(
            latest_snapshot
        )

        difference = SnapshotDifference.compare(
            historical=historical_document,
            latest=latest_document,
        )

        return self._format_difference_context(
            historical_document=historical_document,
            latest_document=latest_document,
            difference=difference,
        )

    def combine(
        self,
        latest_context,
        historical_context=None,
    ):
        """
        組合 Latest Context 與 Historical Context。
        """

        if not isinstance(
            latest_context,
            dict,
        ):
            raise TypeError(
                "latest_context must be a dictionary."
            )

        if "context_text" not in latest_context:
            raise ValueError(
                "latest_context must contain 'context_text'."
            )

        if historical_context is None:
            return latest_context

        if not isinstance(
            historical_context,
            str,
        ):
            raise TypeError(
                "historical_context must be a string."
            )

        historical_context = (
            historical_context.strip()
        )

        if not historical_context:
            return latest_context

        combined_context = dict(
            latest_context
        )

        latest_text = (
            latest_context["context_text"].strip()
        )

        combined_context["context_text"] = (
            f"{latest_text}\n\n"
            f"[Historical Snapshot Context]\n"
            f"{historical_context}"
        )

        return combined_context

    def build(
        self,
        query,
        urls=None,
        historical_snapshot=None,
        latest_snapshot=None,
    ):
        """
        建立 R10.4 Combined RAG Context。
        """

        latest_context = self.build_latest_context(
            query=query,
            urls=urls,
        )

        if (
            historical_snapshot is None
            or latest_snapshot is None
        ):
            return latest_context

        historical_context = (
            self.build_difference_context(
                historical_snapshot=historical_snapshot,
                latest_snapshot=latest_snapshot,
            )
        )

        return self.combine(
            latest_context=latest_context,
            historical_context=historical_context,
        )

    @staticmethod
    def _to_snapshot_document(
        snapshot,
    ):
        """
        將 Snapshot 轉換成 SnapshotDocument。
        """

        if isinstance(
            snapshot,
            SnapshotDocument,
        ):
            return snapshot

        if not isinstance(
            snapshot,
            dict,
        ):
            raise TypeError(
                "snapshot must be a dictionary or SnapshotDocument."
            )

        return SnapshotDocument.from_snapshot(
            snapshot
        )

    @staticmethod
    def _format_difference_context(
        historical_document,
        latest_document,
        difference,
    ):
        """
        將 Snapshot Difference 轉換成 RAG Context Text。
        """

        sections = [
            f"Historical Snapshot Time: "
            f"{historical_document.snapshot_created_at}",
            f"Latest Snapshot Time: "
            f"{latest_document.snapshot_created_at}",
        ]

        if not difference.has_changes:
            sections.append(
                "No content differences were detected."
            )
            return "\n".join(sections)

        if difference.added:
            sections.append(
                "Added Content:\n"
                + "\n".join(
                    difference.added
                )
            )

        if difference.deleted:
            sections.append(
                "Deleted Content:\n"
                + "\n".join(
                    difference.deleted
                )
            )

        if difference.modified:
            modified_sections = []

            for item in difference.modified:
                historical = "\n".join(
                    item["historical"]
                )

                latest = "\n".join(
                    item["latest"]
                )

                modified_sections.append(
                    "Historical:\n"
                    f"{historical}\n"
                    "Latest:\n"
                    f"{latest}"
                )

            sections.append(
                "Modified Content:\n"
                + "\n\n".join(
                    modified_sections
                )
            )

        return "\n\n".join(
            sections
        )


__all__ = [
    "ArchiveRAGContext",
]