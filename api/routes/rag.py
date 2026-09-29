"""
api/routes/rag.py

AutoSearch V7

RAG-8 FastAPI Web Integration

功能:
    GET /rag
        顯示 RAG 問答 Web Page

    POST /rag/query
        執行 RAG Query

架構:
    Browser
        ↓
    FastAPI
        ↓
    RAGQuery
        ↓
    RAG-5 Retriever
        ↓
    RAG-6 Context Builder
        ↓
    RAG-7 LLM Generation
        ↓
    Response
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from rag.rag_query import RAGQuery


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

templates = Jinja2Templates(
    directory="templates",
)

_rag_query = None


def get_rag_query():
    """延遲初始化 RAGQuery，避免 API import 時立即載入 RAG 元件。"""
    global _rag_query

    if _rag_query is None:
        _rag_query = RAGQuery()

    return _rag_query


class RAGQueryRequest(BaseModel):
    query: str
    urls: list[str] | None = None


@router.get(
    "",
    include_in_schema=False,
)
def rag_page(request: Request):
    """顯示 RAG 問答頁面。"""
    return templates.TemplateResponse(
        request=request,
        name="rag/index.html",
        context={
            "project": "AutoSearch V7",
            "page": "RAG 問答",
        },
    )


@router.post("/query")
def rag_query_api(
    request: RAGQueryRequest,
):
    """執行 RAG 查詢並回傳結果。"""
    query = request.query.strip()

    if not query:
        return {
            "answer": "",
            "sources": [],
            "error": "Query cannot be empty.",
        }

    urls = request.urls

    if urls is not None:
        urls = [
            url.strip()
            for url in urls
        ]

    rag = get_rag_query()
    result = rag.run(
        query=query,
        urls=urls,
    )

    print("\n========== RAG API RESULT ==========")
    print("RESULT TYPE:", type(result))
    print("RESULT:", result)

    if isinstance(result, dict):
        print("ANSWER:", result.get("answer"))
        print("SOURCES:", result.get("sources"))
        print("SOURCE REFERENCES:", result.get("source_references"))

    print("====================================\n")

    return result