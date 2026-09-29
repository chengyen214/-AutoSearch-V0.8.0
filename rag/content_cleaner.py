"""
rag/content_cleaner.py

AutoSearch V7

RAG-1.4

Content Cleaning

功能：

    將既有 Parser 產生的 Article content
    做最小必要的內容標準化，
    供後續 RAG-2 Chunking 使用。

資料流程：

    Existing Parser
          ↓
    Article.content
          ↓
    ContentCleaner
          ↓
    Clean Content
          ↓
    RAG-2 Chunking

本階段原則：

    1. 沿用既有 Parser 結果。
    2. 不重新解析 HTML。
    3. 不重新 Crawl。
    4. 不建立新的網站 Parser。
    5. 不猜測並刪除文章正文。
    6. 只做最小內容標準化。
    7. 不修改 Article。
    8. 不處理 Metadata。
    9. 不執行 Chunking。
    10. 不執行 Embedding。
    11. 不使用 ChromaDB。
    12. 不執行 LLM。
"""

import re


class ContentCleaner:
    """
    RAG-1.4 Content Cleaner。

    負責：

        1. 驗證 content
        2. 統一換行
        3. 移除每行頭尾空白
        4. 移除過多空白行
        5. 移除全文頭尾空白

    不負責：

        Parser
        Crawler
        Metadata
        Chunking
        Embedding
        Vector Store
        LLM
    """

    MAX_CONSECUTIVE_NEWLINES = 2

    @classmethod
    def clean(
        cls,
        content
    ):
        """
        清理文章內容。

        Parameters:
            content:
                既有 Parser 產生的文章內容。

        Returns:
            str

        Raises:
            ValueError:
                content 為 None 或空字串。

            TypeError:
                content 不是 str。
        """

        if content is None:
            raise ValueError(
                "Content cannot be None."
            )

        if not isinstance(
            content,
            str
        ):
            raise TypeError(
                "Content must be a str."
            )

        if not content.strip():
            raise ValueError(
                "Content cannot be empty."
            )

        cleaned = content.replace(
            "\r\n",
            "\n"
        )

        cleaned = cleaned.replace(
            "\r",
            "\n"
        )

        lines = cleaned.split(
            "\n"
        )

        normalized_lines = []

        for line in lines:
            normalized_line = line.strip()

            normalized_lines.append(
                normalized_line
            )

        cleaned = "\n".join(
            normalized_lines
        )

        cleaned = re.sub(
            r"\n{3,}",
            "\n\n",
            cleaned
        )

        cleaned = cleaned.strip()

        if not cleaned:
            raise ValueError(
                "Content is empty after cleaning."
            )

        return cleaned


__all__ = [
    "ContentCleaner"
]