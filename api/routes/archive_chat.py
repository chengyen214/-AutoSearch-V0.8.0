"""
api/routes/archive_chat.py

AutoSearch V7

R10.5

Article Archive Chat API

用途：

    提供 Article Archive Viewer
    頁面內 Robot 使用的 Chat API。

資料流程：

    Article Archive Viewer
            ↓
    /archive/chat
            ↓
    ArchiveChatService
            ↓
    R10.1 Snapshot History
            ↓
    R10.4 Archive RAG
            ↓
    RAGQuery
            ↓
    Final Response

Request：

    {
        "url": "https://example.com/article",
        "query": "這篇文章的重點是什麼？",
        "version": null
    }

一般問題：

    version = null

        ↓

    Latest Snapshot
        +
    Latest ChromaDB RAG

歷史問題 / 版本比較：

    version = Snapshot created_at

        ↓

    Latest Snapshot
        +
    Historical Snapshot
        +
    Snapshot Difference
        +
    Latest ChromaDB RAG

本 Router 不負責：

    - MongoDB
    - Snapshot History Query
    - Snapshot Difference
    - ChromaDB
    - Embedding
    - Prompt Construction
    - LLM
"""

from typing import (
    Optional,
)

from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import (
    BaseModel,
)

from services.archive_chat_service import (
    ArchiveChatService,
)

from utils.logger import (
    logger,
)


router = APIRouter(
    prefix="/archive",
    tags=["Archive Chat"],
)


class ArchiveChatRequest(
    BaseModel
):
    """
    Article Archive Robot Request。
    """

    url: str

    query: str

    version: Optional[str] = None


_service = None


def get_archive_chat_service():
    """
    取得 ArchiveChatService。

    使用 Lazy Initialization。
    """

    global _service

    if _service is None:
        _service = ArchiveChatService()

    return _service


@router.post(
    "/chat",
)
def archive_chat(
    request: ArchiveChatRequest,
):
    """
    Article Archive Robot Chat API。

    一般問題：

        version = None

    歷史版本 / 版本比較：

        version = Snapshot created_at
    """

    url = request.url.strip()
    query = request.query.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="Article URL is required.",
        )

    if not query:
        raise HTTPException(
            status_code=400,
            detail="User query is required.",
        )

    service = get_archive_chat_service()

    try:
        result = service.run(
            url=url,
            query=query,
            version=request.version,
        )

        return result

    except ValueError as e:
        logger.warning(
            "Archive Chat validation failed: "
            f"url={url}, "
            f"error={e}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        logger.exception(
            "Archive Chat failed: "
            f"url={url}, "
            f"error={e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Archive Chat failed."
            ),
        )


__all__ = [
    "router",
    "ArchiveChatRequest",
    "get_archive_chat_service",
]