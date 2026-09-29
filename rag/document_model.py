"""
rag/document_model.py

AutoSearch V7

RAG-1.2
RAG-1.3

Document Model + Metadata

功能：

    將 AutoSearch Article
    轉換成 LangChain Document。

    同時建立正式的 RAG Metadata Schema。

資料流程：

    MCP
      ↓
    Article dict
      ↓
    ArticleDocument
      ↓
    LangChain Document
      ↓
    page_content + metadata

RAG Metadata Schema：

    Core Article Metadata：

        1. document_id
        2. title
        3. url
        4. keyword
        5. source
        6. crawl_time

    AI Knowledge Metadata：

        7. ai_summary
        8. ai_category
        9. ai_keywords
        10. ai_importance
        11. ai_confidence

Metadata Mapping：

    Article.document_id
        → metadata.document_id

    Article.title
        → metadata.title

    Article.url
        → metadata.url

    Article.keyword
        → metadata.keyword

    Article.source
        → metadata.source

    Article.crawl_time
        → metadata.crawl_time

    Article.ai_summary
        → metadata.ai_summary

    Article.ai_category
        → metadata.ai_category

    Article.ai_keywords
        → metadata.ai_keywords

    Article.ai_importance
        → metadata.ai_importance

    Article.ai_confidence
        → metadata.ai_confidence

本階段不負責：

    1. MCP
    2. Database
    3. SQL
    4. Chunking
    5. Embedding
    6. ChromaDB
    7. Retriever
    8. LLM
"""

from langchain_core.documents import Document


class ArticleDocument:
    """
    RAG-1.2 Article → LangChain Document。

    RAG-1.3 Metadata：
        定義並建立正式 RAG Metadata Schema。

    負責：

        1. 接收 Article dict
        2. 驗證必要欄位
        3. 建立 LangChain Document
        4. 建立正式 RAG Metadata
        5. 將 Article 欄位映射到 Document metadata
    """

    REQUIRED_FIELDS = (
        "document_id",
        "title",
        "url",
        "content",
    )

    METADATA_FIELDS = (
        "document_id",
        "title",
        "url",
        "keyword",
        "source",
        "crawl_time",
        "ai_summary",
        "ai_category",
        "ai_keywords",
        "ai_importance",
        "ai_confidence",
    )

    @classmethod
    def from_article(
        cls,
        article
    ):
        """
        將 Article dict
        轉換成 LangChain Document。

        Parameters:
            article:
                AutoSearch Article dict。

        Returns:
            langchain_core.documents.Document

        Raises:
            ValueError:
                Article 缺少必要欄位。

            TypeError:
                Article 不是 dict。
        """

        if article is None:
            raise ValueError(
                "Article cannot be None."
            )

        if not isinstance(
            article,
            dict
        ):
            raise TypeError(
                "Article must be a dict."
            )

        for field in cls.REQUIRED_FIELDS:
            value = article.get(
                field
            )

            if value is None:
                raise ValueError(
                    f"Article field "
                    f"'{field}' is missing."
                )

            if isinstance(
                value,
                str
            ) and not value.strip():
                raise ValueError(
                    f"Article field "
                    f"'{field}' is empty."
                )

        page_content = str(
            article["content"]
        )

        metadata = {
            "document_id": article[
                "document_id"
            ],
            "title": article[
                "title"
            ],
            "url": article[
                "url"
            ],
            "keyword": article.get(
                "keyword"
            ),
            "source": article.get(
                "source"
            ),
            "crawl_time": article.get(
                "crawl_time"
            ),
            "ai_summary": article.get(
                "ai_summary"
            ),
            "ai_category": article.get(
                "ai_category"
            ),
            "ai_keywords": article.get(
                "ai_keywords"
            ),
            "ai_importance": article.get(
                "ai_importance"
            ),
            "ai_confidence": article.get(
                "ai_confidence"
            ),
        }

        return Document(
            page_content=page_content,
            metadata=metadata
        )


__all__ = [
    "ArticleDocument"
]