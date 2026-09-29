"""
rag/generation/answer_generator.py

AutoSearch V7

RAG-7.5

Answer Generation

功能：

1. 接收 RAG-7.4 LLM Response
2. 接收 RAG-6 Context
3. 建立最終 Answer Text
4. 解析 LLM 回答中的 Source References
5. 將 Source Index 對應回 RAG-6 Context
6. 回傳 Answer + Source References

本層不負責：

1. Retrieval
2. Query Embedding
3. ChromaDB
4. Context Building
5. Prompt Construction
6. LLM Invocation
7. Trend Analysis
8. Report Generation
9. Query Understanding
10. Query Planning
"""

import re


class AnswerGenerator:
    """
    RAG-7.5 Answer Generation Layer。

    將：

        RAG-6 Context
            +
        RAG-7.4 LLM Response

    整理成：

        Answer Text
            +
        Source References
    """

    # Source Reference Pattern
    # 支援 [Source 1]、[Source 2]、【Source 1】、【Source 2】

    SOURCE_PATTERN = re.compile(
        r"(?:\[|【)Source\s+(\d+)(?:\]|】)",
        re.IGNORECASE,
    )

    def generate(
        self,
        llm_response,
        context,
    ):
        """
        建立最終 Answer。

        Parameters
        ----------
        llm_response : str
            RAG-7.4 LLMInvoker 回傳的 LLM Response。

        context : dict
            RAG-6 Context。

        Returns
        -------
        dict
            {
                "answer_text": str,
                "source_references": list
            }
        """

        self._validate_llm_response(
            llm_response
        )

        self._validate_context(
            context
        )

        answer_text = self._build_answer_text(
            llm_response
        )

        source_references = (
            self._build_source_references(
                answer_text,
                context,
            )
        )

        return {
            "answer_text": answer_text,
            "source_references": source_references,
        }

    @staticmethod
    def _build_answer_text(
        llm_response,
    ):
        """
        建立最終 Answer Text。

        RAG-7.5 不重新生成內容，
        僅進行基本文字清理。
        """

        return llm_response.strip()

    def _build_source_references(
        self,
        answer_text,
        context,
    ):
        """
        從 LLM Answer 中解析：

            [Source 1]
            [Source 3]

        以及：

            【Source 1】
            【Source 3】

        再對應回 RAG-6 Context entries。

        回傳順序依照 LLM 實際引用順序，
        並自動移除重複 Source。
        """

        source_indexes = (
            self._extract_source_indexes(
                answer_text
            )
        )

        if not source_indexes:
            return []

        entries = context["entries"]

        entry_map = {
            entry["source_index"]: entry
            for entry in entries
        }

        source_references = []

        for source_index in source_indexes:

            entry = entry_map.get(
                source_index
            )

            if entry is None:
                continue

            source_references.append(
                {
                    "source_index": (
                        entry["source_index"]
                    ),
                    "document_id": (
                        entry["document_id"]
                    ),
                    "chunk_index": (
                        entry["chunk_index"]
                    ),
                    "title": (
                        entry["title"]
                    ),
                    "url": (
                        entry["url"]
                    ),
                }
            )

        return source_references

    def _extract_source_indexes(
        self,
        answer_text,
    ):
        """
        解析 LLM Response 中的：

            [Source 1]
            [Source 2]

        以及：

            【Source 1】
            【Source 2】
        """

        matches = (
            self.SOURCE_PATTERN.findall(
                answer_text
            )
        )

        source_indexes = []

        for match in matches:

            source_index = int(match)

            if source_index not in source_indexes:
                source_indexes.append(
                    source_index
                )

        return source_indexes

    @staticmethod
    def _validate_llm_response(
        llm_response,
    ):
        """
        驗證 LLM Response。
        """

        if llm_response is None:
            raise ValueError(
                "llm_response cannot be None"
            )

        if not isinstance(
            llm_response,
            str,
        ):
            raise TypeError(
                "llm_response must be a string"
            )

        if not llm_response.strip():
            raise ValueError(
                "llm_response cannot be empty"
            )

    @staticmethod
    def _validate_context(
        context,
    ):
        """
        驗證 RAG-6 Context。
        """

        if context is None:
            raise ValueError(
                "context cannot be None"
            )

        if not isinstance(
            context,
            dict,
        ):
            raise TypeError(
                "context must be a dictionary"
            )

        required_fields = (
            "entries",
            "context_text",
            "count",
        )

        for field in required_fields:

            if field not in context:
                raise ValueError(
                    f"context missing required field: "
                    f"{field}"
                )

        entries = context["entries"]

        if not isinstance(
            entries,
            list,
        ):
            raise TypeError(
                "context entries must be a list"
            )

        if context["count"] != len(entries):
            raise ValueError(
                "context count does not match "
                "entries length"
            )

        for entry in entries:

            if not isinstance(
                entry,
                dict,
            ):
                raise TypeError(
                    "context entry must be a dictionary"
                )

            required_entry_fields = (
                "source_index",
                "document_id",
                "chunk_index",
                "title",
                "url",
                "content",
            )

            for field in required_entry_fields:

                if field not in entry:
                    raise ValueError(
                        "context entry missing "
                        f"required field: {field}"
                    )


__all__ = [
    "AnswerGenerator",
]