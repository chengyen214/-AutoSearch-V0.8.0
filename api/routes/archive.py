"""
api/routes/archive.py

AutoSearch V4

P2.3.9 API/UI Integration
P2.4.2 Composite Archive Search API
P2.4.3 Composite Search Web UI

用途:
    提供 Knowledge Archive Web API
    提供 Knowledge Archive Web UI
    提供 Composite Archive Search API
    提供 Composite Archive Search Web UI

架構:
    Browser
        ↓
    /archive/search
        ↓
    Archive Search Web UI
        ↓
    /archive/search/api
        ↓
    Composite Archive Search API
        ↓
    ArchiveWebService
        ↓
    Repository / Knowledge History
        ↓
    Database

注意:
    API Layer 不直接操作 Database。

路由:
    GET /archive/ui
        Knowledge Archive Web UI

    GET /archive/search
        Composite Archive Search Web UI

    GET /archive/search/ui
        Composite Archive Search Web UI
        相容入口

    GET /archive/search/api
        Composite Archive Search JSON API

Composite Search 支援:
    keyword
    url
    source
    date_from
    date_to
    year
    month
    category
    importance_min
    importance_max

AI Result:
    articles.ai_summary
    articles.ai_category
    articles.ai_keywords
    articles.ai_importance
    articles.ai_model
    articles.ai_version
    articles.ai_analyze_time
    articles.ai_confidence
    articles.ai_status
"""

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)
from fastapi.templating import Jinja2Templates

from services.archive_web_service import (
    ArchiveWebService,
)

router = APIRouter(
    prefix="/archive",
    tags=["Archive"],
)

templates = Jinja2Templates(
    directory="templates",
)

_service = None


def get_archive_service():
    """
    取得 ArchiveWebService。

    使用 Lazy Initialization，
    避免 API import 時立即建立 Repository。
    """
    global _service

    if _service is None:
        _service = ArchiveWebService()

    return _service


@router.get(
    "/ui",
    include_in_schema=False,
)
def archive_ui(
    request: Request,
):
    """
    Knowledge Archive Web UI。

    GET /archive/ui
    """
    service = get_archive_service()

    statistics = service.get_statistics()
    articles = service.get_articles(
        limit=20,
    )

    return templates.TemplateResponse(
        request=request,
        name="archive/index.html",
        context={
            "statistics": statistics,
            "articles": articles,
            "version": "V4-P2.4.3",
        },
    )


def _render_search_ui(
    request: Request,
):
    """
    Composite Archive Search Web UI 共用入口。

    使用:
        GET /archive/search
        GET /archive/search/ui

    此路由只負責回傳 HTML。
    Composite Search JSON API 使用 GET /archive/search/api。
    """
    return templates.TemplateResponse(
        request=request,
        name="archive/search.html",
        context={
            "project": "AutoSearch V4",
            "version": "4.0",
            "page": "Composite Archive Search",
        },
    )


@router.get(
    "/search",
    include_in_schema=False,
)
def search_archive_ui(
    request: Request,
):
    """
    Composite Archive Search Web UI。

    GET /archive/search

    Browser 開啟此 URL 時顯示搜尋頁面。
    Search UI 內部再呼叫 GET /archive/search/api。
    """
    return _render_search_ui(request)


@router.get(
    "/search/ui",
    include_in_schema=False,
)
def search_ui(
    request: Request,
):
    """
    Composite Archive Search Web UI。

    GET /archive/search/ui

    與 GET /archive/search 使用相同 UI。
    """
    return _render_search_ui(request)


@router.get("/articles")
def get_articles(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    ),
):
    """取得 Archive Article。GET /archive/articles。"""
    service = get_archive_service()

    return service.get_articles(
        limit=limit,
    )


@router.get("/articles/page")
def get_articles_with_pagination(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
):
    """分頁取得 Archive Articles。"""
    service = get_archive_service()

    return service.get_articles_with_pagination(
        page=page,
        page_size=page_size,
    )


@router.get("/articles/{article_id}/versions")
def get_versions(
    article_id: int,
):
    """取得 Article 所有 Archive Versions。"""
    service = get_archive_service()

    return service.get_versions(article_id)


@router.get("/articles/{article_id}/versions/latest")
def get_latest_version(
    article_id: int,
):
    """取得 Article 最新 Version。"""
    service = get_archive_service()

    result = service.get_latest_version(article_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Latest archive version not found",
        )

    return result


@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
):
    """取得指定 Article。"""
    service = get_archive_service()

    result = service.get_article(article_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Archive article not found",
        )

    return result


@router.get("/date/{archive_date}")
def get_by_date(
    archive_date: str,
):
    """依日期取得 Archive。"""
    service = get_archive_service()

    return service.get_by_date(archive_date)


@router.get("/month/{year}/{month}")
def get_by_month(
    year: int,
    month: int,
):
    """依月份取得 Archive。"""
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12",
        )

    service = get_archive_service()

    return service.get_by_month(year, month)


@router.get("/year/{year}")
def get_by_year(
    year: int,
):
    """依年份取得 Archive。"""
    service = get_archive_service()

    return service.get_by_year(year)


@router.get("/source/{source}")
def get_by_source(
    source: str,
):
    """依來源取得 Archive。"""
    service = get_archive_service()

    return service.get_by_source(source)


def _composite_archive_search(
    keyword: str | None = None,
    url: str | None = None,
    source: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    year: int | None = None,
    month: int | None = None,
    category: str | None = None,
    importance_min: float | None = None,
    importance_max: float | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    Composite Archive Search 共用實作。

    所有搜尋條件皆為 Optional。

    支援:
        keyword, url, source, date_from, date_to
        year, month, category
        importance_min, importance_max

    API Layer 不直接操作 Database。
    Repository / Service 負責取得資料。
    """
    service = get_archive_service()

    if keyword is not None:
        keyword = str(keyword).strip()
        if not keyword:
            keyword = None

    if url is not None:
        url = str(url).strip()
        if not url:
            url = None

    if source is not None:
        source = str(source).strip()
        if not source:
            source = None

    if category is not None:
        category = str(category).strip()
        if not category:
            category = None

    if (
        importance_min is not None
        and importance_max is not None
        and importance_min > importance_max
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "importance_min cannot be "
                "greater than importance_max"
            ),
        )

    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "date_from cannot be "
                "greater than date_to"
            ),
        )

    if (
        month is not None
        and (month < 1 or month > 12)
    ):
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12",
        )

    result = service.composite_search(
        keyword=keyword,
        url=url,
        source=source,
        date_from=date_from,
        date_to=date_to,
        year=year,
        month=month,
        category=category,
        importance_min=importance_min,
        importance_max=importance_max,
        page=page,
        page_size=page_size,
    )

    if result is None:
        return {
            "results": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "filters": {
                "keyword": keyword,
                "url": url,
                "source": source,
                "date_from": date_from,
                "date_to": date_to,
                "year": year,
                "month": month,
                "category": category,
                "importance_min": importance_min,
                "importance_max": importance_max,
            },
        }

    return result


@router.get("/search/api")
def composite_search_api(
    keyword: str | None = Query(None),
    url: str | None = Query(
        None,
        description="Optional URL search filter",
    ),
    source: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(
        None,
        ge=1,
        le=12,
    ),
    category: str | None = Query(None),
    importance_min: float | None = Query(
        None,
        ge=0,
        le=10,
    ),
    importance_max: float | None = Query(
        None,
        ge=0,
        le=10,
    ),
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
):
    """
    Composite Archive Search JSON API。

    GET /archive/search/api

    Optional filters:
        keyword, url, source, date_from, date_to
        year, month, category
        importance_min, importance_max

    Examples:
        /archive/search/api?keyword=TSMC
        /archive/search/api?url=tsmc.com
        /archive/search/api?keyword=TSMC&url=tsmc.com
        /archive/search/api?source=CNA&url=cna.com.tw
        /archive/search/api?category=Semiconductor

    AI Result:
        results[*].ai_summary

    回傳 results、total、page、page_size 與 filters。
    """
    return _composite_archive_search(
        keyword=keyword,
        url=url,
        source=source,
        date_from=date_from,
        date_to=date_to,
        year=year,
        month=month,
        category=category,
        importance_min=importance_min,
        importance_max=importance_max,
        page=page,
        page_size=page_size,
    )


@router.get("/count")
def count_archive():
    """取得 Archive 數量。"""
    service = get_archive_service()

    return {
        "count": service.count(),
    }


@router.get("/count/articles")
def count_articles():
    """取得 Article 數量。"""
    service = get_archive_service()

    return {
        "count": service.count_articles(),
    }


@router.get("/count/source/{source}")
def count_by_source(
    source: str,
):
    """取得指定 Source 的 Archive 數量。"""
    service = get_archive_service()

    return {
        "source": source,
        "count": service.count_by_source(source),
    }


@router.get("/count/date/{archive_date}")
def count_by_date(
    archive_date: str,
):
    """取得指定日期的 Archive 數量。"""
    service = get_archive_service()

    return {
        "date": archive_date,
        "count": service.count_by_date(archive_date),
    }


@router.get("/statistics")
def get_statistics():
    """取得 Archive Statistics。"""
    service = get_archive_service()

    return service.get_statistics()


@router.get("/knowledge/{article_id}/history")
def get_knowledge_history(
    article_id: int,
):
    """取得 Article Knowledge History。"""
    service = get_archive_service()

    return service.get_knowledge_history(article_id)


@router.get("/knowledge/{article_id}/latest")
def get_latest_knowledge(
    article_id: int,
):
    """取得 Article 最新 Knowledge。"""
    service = get_archive_service()

    result = service.get_latest_knowledge(article_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge not found",
        )

    return result


@router.get("/knowledge/{article_id}/evolution")
def get_knowledge_evolution(
    article_id: int,
):
    """取得完整 Knowledge Evolution。"""
    service = get_archive_service()

    return service.get_knowledge_evolution(article_id)


@router.get("/health")
def archive_health():
    """Archive API Health Check。"""
    return {
        "status": "ok",
        "service": "archive",
        "version": "V4-P2.4.3",
    }