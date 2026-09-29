"""
api/main.py

AutoSearch V4 / V5

FastAPI API + Web UI Layer

P3.10 Final

功能:

V2.5:
    Article API

V3:
    AI Analysis Retrieval API

V4 P1:
    P1.4:
        Knowledge Retrieval API

    P1.5:
        Knowledge Ranking API

    P1.6:
        Knowledge Intelligence API

    P1.7:
        Intelligent Search API
        Semantic Search API

V4 P2:
    P2.1:
        Hybrid Search API

    P2.2:
        Search Index API

    P2.3:
        Knowledge Archive API
        Knowledge Archive Web UI
        Historical Search API

    P2.4:
        Knowledge Archive Management API
        Composite Archive Search Service
        Composite Archive Search Web UI

V4 P3:
    P3.1:
        Article Management API

    P3.2:
        Archive Management API

    P3.3:
        Article Version API

    P3.4:
        AI Task Management API

    P3.5:
        AI Analysis API

    P3.6:
        Knowledge API

    P3.7:
        Knowledge Score API

    P3.8:
        Search API

    P3.9:
        Ranking API

    P3.10:
        System / Health API

V5:
    Target Management API


Web UI:

    /
        AutoSearch V4 Dashboard

    /archive/ui
        Knowledge Archive

    /archive/search
        Composite Archive Search


Swagger:

    /docs


Run:

    uvicorn api.main:app --reload
"""


# ==================================================
# Imports
# ==================================================

from fastapi import (
    FastAPI,
    Request,
)

from fastapi.templating import (
    Jinja2Templates,
)


# ==================================================
# Templates
# ==================================================

templates = Jinja2Templates(
    directory="templates"
)


# ==================================================
# OpenAPI Tags
# ==================================================

tags_metadata = [

    # ----------------------------------
    # V2.5 / V3
    # ----------------------------------

    {
        "name": "Article API",
        "description":
            "文章資料與 Article API",
    },

    {
        "name": "AI Analysis",
        "description":
            "AI Analysis 查詢與分析結果 API",
    },


    # ----------------------------------
    # V4 P1
    # ----------------------------------

    {
        "name": "Knowledge API",
        "description":
            "Knowledge Archive / Knowledge Retrieval API",
    },

    {
        "name": "Knowledge Ranking",
        "description":
            "Knowledge Ranking 與 Knowledge Score Filter API",
    },

    {
        "name": "Knowledge Score",
        "description":
            "Knowledge Score 管理與查詢 API",
    },

    {
        "name": "Intelligence API",
        "description":
            "Knowledge Intelligence Service API",
    },

    {
        "name": "Search API",
        "description":
            "Keyword / Entity / Hybrid / Ranked Search API",
    },


    # ----------------------------------
    # V4 P2
    # ----------------------------------

    {
        "name": "Search Index",
        "description":
            "Search Index 建立、更新與查詢 API",
    },

    {
        "name": "Archive",
        "description":
            "Knowledge Archive API 與 Web UI",
    },

    {
        "name": "Archive Management",
        "description":
            "Knowledge Archive Management API",
    },

    {
        "name": "Historical Search",
        "description":
            "Knowledge Archive Historical Search API",
    },


    # ----------------------------------
    # V4 P3
    # ----------------------------------

    {
        "name": "Article Management",
        "description":
            "Article Management API",
    },

    {
        "name": "Article Version",
        "description":
            "Article Version 與 Version History API",
    },

    {
        "name": "AI Task Management",
        "description":
            "AI Task Queue、Pending Task 與 AI Task Management API",
    },

    {
        "name": "Ranking API",
        "description":
            "Search Ranking、Score Calculator 與 Final Search Score API",
    },

    {
        "name": "System",
        "description":
            "System Status、Health Check 與 Version API",
    },


    # ----------------------------------
    # V5
    # ----------------------------------

    {
        "name": "Target Management",
        "description":
            "Target 建立、查詢、刪除與狀態管理 API",
    },

]


# ==================================================
# Routers
# ==================================================

from api.routes import (

    articles,

    ai_analysis,

    targets,

    knowledge,

    knowledge_ranking,

    intelligence,

    intelligent_search,

    semantic_search,

    hybrid_search,

    search_index,

    archive,

    archive_viewer,

    archive_chat,

    archive_management,

    historical_search,

    ai_tasks,

    search,

    ranking,

    system,
    
    rag,
)


# ==================================================
# FastAPI Application
# ==================================================

app = FastAPI(

    title="AutoSearch V4 API",

    version="4.0",

    description=(
        "AutoSearch V4 "
        "Knowledge Archive "
        "Management and Intelligence API"
    ),

    openapi_tags=tags_metadata,

)


# ==================================================
# Web Dashboard
# ==================================================

@app.get(
    "/",
    include_in_schema=False,
)
def dashboard(
    request: Request,
):
    """
    AutoSearch V4 Web Dashboard。
    """

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={

            "project":
                "AutoSearch V4",

            "version":
                "4.0",

        },

    )


# ==================================================
# Target Management Web UI
# ==================================================

@app.get(
    "/targets/ui",
    include_in_schema=False,
)
def targets_ui(
    request: Request,
):
    """
    AutoSearch V5

    Target Management Web UI。
    """

    return templates.TemplateResponse(

        request=request,

        name="targets/index.html",

        context={

            "project":
                "AutoSearch V5",

            "version":
                "5.0",

            "page":
                "Target Management",

        },

    )


# ==================================================
# Knowledge Archive Web UI
# ==================================================

@app.get(
    "/archive/ui",
    include_in_schema=False,
)
def archive_ui(
    request: Request,
):
    """
    AutoSearch V4

    Knowledge Archive Web UI。
    """

    return templates.TemplateResponse(

        request=request,

        name="archive/index.html",

        context={

            "project":
                "AutoSearch V4",

            "version":
                "4.0",

            "page":
                "Knowledge Archive",

        },

    )


# ==================================================
# Composite Archive Search Web UI
# ==================================================

@app.get(
    "/archive/search",
    include_in_schema=False,
)
def archive_search_page(
    request: Request,
):
    """
    AutoSearch V4

    P2.4

    Composite Archive Search Web UI。
    """

    return templates.TemplateResponse(

        request=request,

        name="archive/search.html",

        context={

            "project":
                "AutoSearch V4",

            "version":
                "4.0",

            "page":
                "Composite Archive Search",

        },

    )


# ==================================================
# API Root
# ==================================================

@app.get(
    "/api",
    tags=[
        "System",
    ],
)
def api_root():
    """
    AutoSearch V4 API Root。
    """

    return {

        "project":
            "AutoSearch V4",

        "version":
            "4.0",

        "stage":
            "P3.10 + V5 Target Management",

        "status":
            "running",

        "modules": [

            # ------------------------------
            # V2.5 / V3
            # ------------------------------

            "Article API",

            "AI Analysis",


            # ------------------------------
            # V4 P1
            # ------------------------------

            "Knowledge Retrieval",

            "Knowledge Ranking",

            "Knowledge Score",

            "Knowledge Intelligence",

            "Intelligent Search",

            "Semantic Search",


            # ------------------------------
            # V4 P2
            # ------------------------------

            "Hybrid Search",

            "Search Index",

            "Knowledge Archive",

            "Knowledge Archive Management",

            "Historical Search",

            "Composite Archive Search",


            # ------------------------------
            # V4 P3
            # ------------------------------

            "Article Management",

            "Article Version",

            "AI Task Management",

            "Knowledge API",

            "Knowledge Score API",

            "Search API",

            "Ranking API",

            "System / Health API",


            # ------------------------------
            # V5
            # ------------------------------

            "Target Management",

        ],

        "links": {

            "dashboard":
                "/",

            "docs":
                "/docs",

            "openapi":
                "/openapi.json",

            "archive":
                "/archive/ui",

            "archive_search":
                "/archive/search",

            "historical_search":
                "/historical-search",

            "archive_management":
                "/management/archive",

            "ai_analysis":
                "/ai/analysis",

            "ai_tasks":
                "/ai/tasks",

            "knowledge":
                "/knowledge",

            "knowledge_ranking":
                "/knowledge/ranking",

            "search":
                "/search",

            "ranking":
                "/ranking",

            "system":
                "/system",

            "targets":
                "/targets",

        },

    }


# ==================================================
# Router Register
# ==================================================


# ==================================================
# V2.5 / V3
# Article API
# ==================================================

app.include_router(
    articles.router
)


# ==================================================
# V3 / V4 P3.5
# AI Analysis API
# ==================================================

app.include_router(
    ai_analysis.router
)


# ==================================================
# V4 P1.4
# Knowledge Retrieval API
# ==================================================

app.include_router(
    knowledge.router
)


# ==================================================
# V4 P1.5
# Knowledge Ranking API
# ==================================================

app.include_router(
    knowledge_ranking.router
)


# ==================================================
# V4 P1.6
# Knowledge Intelligence API
# ==================================================

app.include_router(
    intelligence.router
)


# ==================================================
# V4 P1.7
# Intelligent Search API
# ==================================================

app.include_router(
    intelligent_search.router
)


# ==================================================
# V4 P1.7
# Semantic Search API
# ==================================================

app.include_router(
    semantic_search.router
)


# ==================================================
# V4 P2.1
# Hybrid Search API
# ==================================================

app.include_router(
    hybrid_search.router
)


# ==================================================
# V4 P2.2
# Search Index API
# ==================================================

app.include_router(
    search_index.router
)


# ==================================================
# V4 P2.3
# Knowledge Archive API
# ==================================================

app.include_router(
    archive.router
)


# ==================================================
# V5
# Archive Viewer
# ==================================================

app.include_router(
    archive_viewer.router
)


# ==================================================
# V7
# R10.5
# Article Archive Chat API
# ==================================================

app.include_router(
    archive_chat.router
)


# ==================================================
# V4 P2.4
# Knowledge Archive Management API
# ==================================================

app.include_router(
    archive_management.router
)


# ==================================================
# V4 P2.3
# Historical Search API
# ==================================================

app.include_router(
    historical_search.router
)


# ==================================================
# V4 P3.4
# AI Task Management API
# ==================================================

app.include_router(
    ai_tasks.router
)


# ==================================================
# V4 P3.1
# Article Management API
# ==================================================
#
# 注意:
#
# 如果 articles.py 已經同時包含
# Article Management API，
# 不需要另外 include。
#
# 目前沿用 articles.router。
#
# ==================================================


# ==================================================
# V4 P3.6
# Knowledge API
# ==================================================
#
# knowledge.router 已於 P1.4
# 註冊。
#
# P3.6 擴充後仍沿用同一 Router。
#
# ==================================================


# ==================================================
# V4 P3.7
# Knowledge Score API
# ==================================================
#
# 若目前 Knowledge Score API
# 已整合在 knowledge_ranking.router，
# 不需要重複註冊。
#
# ==================================================


# ==================================================
# V4 P3.8
# Search API
# ==================================================

app.include_router(
    search.router
)


# ==================================================
# V4 P3.9
# Ranking API
# ==================================================

app.include_router(
    ranking.router
)


# ==================================================
# V4 P3.10
# System / Health API
# ==================================================

app.include_router(
    system.router
)


# ==================================================
# V5
# Target Management API
# ==================================================

app.include_router(
    targets.router
)


# ==================================================
# V7
# RAG API
# ==================================================

app.include_router(
    rag.router
)