"""
api/routes/archive_viewer.py

AutoSearch V5

Archive Viewer

用途：

    提供獨立的 Archive Article Viewer。

核心設計：

    Search UI
        |
        | 點擊文章標題
        v
    /archive/view?url=...
        |
        v
    MongoDB
        |
        v
    raw_html collection
        |
        +-----------------------------+
        |                             |
        v                             v
    Snapshot History              HTML = None
        |                             |
        v                             v
    viewer.html

使用者選擇 Snapshot：

    /archive/view?
        url=...
        &version=2026-08-29T14:20:00Z
        |
        v
    viewer.html
        |
        v
    iframe
        |
        v
    /archive/snapshot?
        url=...
        &version=...
        |
        v
    MongoDB raw_html
        |
        v
    Raw HTML Response
        |
        v
    Browser Render

重要設計：

    1. 本 Router 不使用 api/routes/archive.py。

    2. 本 Router 不使用 ArchiveWebService。

    3. 本 Router 不使用 ArchiveViewerService。

    4. 本 Router 不使用 RawHTMLRepository。

    5. 本 Router 直接使用 MongoDB。

    6. Snapshot Identity：

           URL
           +
           created_at

    7. version 不代表：

           1
           2
           3

       version 代表：

           created_at

    8. 初次進入：

           /archive/view?url=...

       只查詢 Snapshot History。

       不載入 HTML。

    9. 指定版本：

           /archive/view?
               url=...
               &version=2026-08-29T14:20:00Z

       Viewer UI 載入後，
       iframe 再向：

           /archive/snapshot

       取得 MongoDB 中的 Raw HTML。

    10. /archive/snapshot：

           不使用 srcdoc。

           直接：

               MongoDB
                   ↓
               Raw HTML
                   ↓
               HTTP text/html
                   ↓
               Browser Render

    11. Snapshot HTML 中：

           CSS
           Image

       不再直接依賴真實網站。

       對應 MongoDB：

           resources.css[]
           resources.images[]

       改由 Archive Viewer 自己提供。

    12. MongoDB Snapshot 本身不修改。

    13. 原始 HTML 不修改。

    14. Resource URL 只在 HTTP Response
        動態改寫。

    15. Snapshot HTML 中的 HTTP/HTTPS Link：

           改寫成：

           http://127.0.0.1:8000/archive/view?url=...

       並以新分頁開啟。

       該 URL 的 Archive Viewer
       再由使用者選擇 Snapshot。
"""

from datetime import (
    datetime,
    timezone,
)

from html import (
    escape,
    unescape,
)

import re

from typing import (
    Any,
    Optional,
)

from urllib.parse import (
    quote,
    unquote,
    urljoin,
    urlsplit,
)

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)

from fastapi.responses import (
    RedirectResponse,
    Response,
)

from fastapi.templating import (
    Jinja2Templates,
)

from pymongo import (
    MongoClient,
)

from config.mongo_config import (
    MONGO_URI,
    MONGO_DATABASE,
    MONGO_RAW_HTML_COLLECTION,
)

from utils.logger import (
    logger,
)

router = APIRouter(
    prefix="/archive",
    tags=["Archive Viewer"],
)

templates = Jinja2Templates(
    directory="templates",
)

_client: Optional[MongoClient] = None


def get_mongo_collection():
    """
    取得 MongoDB Raw HTML Collection。

    使用 Lazy Initialization。
    """

    global _client

    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI is not configured."
        )

    if not MONGO_DATABASE:
        raise RuntimeError(
            "MONGO_DATABASE is not configured."
        )

    if not MONGO_RAW_HTML_COLLECTION:
        raise RuntimeError(
            "MONGO_RAW_HTML_COLLECTION "
            "is not configured."
        )

    if _client is None:
        logger.info(
            "Archive Viewer connecting to MongoDB: "
            f"database={MONGO_DATABASE}, "
            f"collection={MONGO_RAW_HTML_COLLECTION}"
        )

        _client = MongoClient(
            MONGO_URI,
        )

    database = _client[
        MONGO_DATABASE
    ]

    collection = database[
        MONGO_RAW_HTML_COLLECTION
    ]

    return collection


def normalize_url(
    url: str | None,
) -> str | None:
    """
    正規化 Archive Viewer URL。

    支援：

        正常 URL

        Markdown Link：

            [https://example.com](https://example.com)
    """

    if url is None:
        return None

    url = str(
        url
    ).strip()

    if not url:
        return None

    if (
        url.startswith("[")
        and "](" in url
        and url.endswith(")")
    ):
        close_bracket = url.find(
            "]("
        )

        if close_bracket > 0:
            markdown_url = url[
                close_bracket + 2:
                -1
            ].strip()

            if markdown_url:
                url = markdown_url

    return url


def normalize_created_at(
    created_at: Any,
) -> datetime | None:
    """
    將 created_at 統一成：

        timezone-aware UTC datetime。
    """

    if created_at is None:
        return None

    if isinstance(
        created_at,
        datetime,
    ):
        if created_at.tzinfo is None:
            return created_at.replace(
                tzinfo=timezone.utc,
            )

        return created_at.astimezone(
            timezone.utc,
        )

    if isinstance(
        created_at,
        str,
    ):
        value = created_at.strip()

        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            logger.warning(
                "Archive Viewer invalid "
                "created_at: "
                f"{created_at}"
            )

            return None

        if parsed.tzinfo is None:
            return parsed.replace(
                tzinfo=timezone.utc,
            )

        return parsed.astimezone(
            timezone.utc,
        )

    logger.warning(
        "Archive Viewer unsupported "
        "created_at type: "
        f"{type(created_at)}"
    )

    return None


def format_created_at(
    created_at: Any,
) -> str | None:

    normalized = normalize_created_at(
        created_at
    )

    if normalized is None:
        return None

    return normalized.isoformat()


def build_archive_view_url(
    target_url: str,
    archive_base_url: str,
    version: str | None = None,
) -> str:
    """
    建立完整 Archive Viewer URL。

    例如：

        target_url：

            https://www.digitimes.com.tw/
            research/report-category/?CnlID=3&cat=ICM

        archive_base_url：

            http://127.0.0.1:8000

        結果：

            http://127.0.0.1:8000/archive/view?
            url=https%3A%2F%2Fwww.digitimes.com.tw%2F...
    """

    target_url = normalize_url(
        target_url
    )

    if not target_url:
        return archive_base_url + "/archive/view"

    parsed = urlsplit(
        target_url
    )

    target_url_without_fragment = (
        parsed._replace(
            fragment=""
        ).geturl()
    )

    archive_url = (
        archive_base_url.rstrip("/")
        + "/archive/view?url="
        + quote(
            target_url_without_fragment,
            safe="",
        )
    )

    if version:
        archive_url += (
            "&version="
            + quote(
                version,
                safe="",
            )
        )

    return archive_url


def build_archive_snapshot_url(
    target_url: str,
    version: str,
    archive_base_url: str,
) -> str:
    """
    建立 Archive Snapshot URL。
    """

    return (
        archive_base_url.rstrip("/")
        + "/archive/snapshot?url="
        + quote(
            target_url,
            safe="",
        )
        + "&version="
        + quote(
            version,
            safe="",
        )
    )


def get_archive_base_url(
    request: Request,
) -> str:
    """
    根據目前 AutoSearch Request 建立
    Archive Viewer Base URL。

    例如：

        http://127.0.0.1:8000

    不使用：

        archived article 的 domain。

    因此：

        https://www.digitimes.com.tw

    只會作為 target article URL，

    不會變成 Archive Viewer Host。
    """

    return (
        f"{request.url.scheme}"
        f"://"
        f"{request.url.netloc}"
    )


def find_snapshot_history(
    url: str,
) -> list[dict[str, Any]]:
    """
    查詢指定 URL 的所有 Raw HTML Snapshot。

    只查詢 Snapshot Metadata。

    不載入：

        html
        resources
    """

    collection = get_mongo_collection()

    try:
        cursor = collection.find(
            {
                "url": url,
            },
            {
                "_id": 1,
                "created_at": 1,
            },
        ).sort(
            "created_at",
            -1,
        )

        versions = []
        seen_versions = set()

        for document in cursor:
            created_at = normalize_created_at(
                document.get(
                    "created_at"
                )
            )

            if created_at is None:
                continue

            version = created_at.isoformat()

            if version in seen_versions:
                continue

            seen_versions.add(
                version
            )

            versions.append({
                "version": version,
                "created_at": version,
            })

        logger.info(
            "Archive Viewer snapshot history: "
            f"url={url}, "
            f"count={len(versions)}"
        )

        return versions

    except Exception as e:
        logger.exception(
            "Archive Viewer failed to query "
            "Snapshot History: "
            f"url={url}, "
            f"error={e}"
        )

        raise


def find_latest_snapshot_version(
    url: str,
) -> str | None:
    """
    查詢指定 URL 最新的 Snapshot。
    """

    collection = get_mongo_collection()

    try:
        document = collection.find_one(
            {
                "url": url,
            },
            {
                "_id": 0,
                "created_at": 1,
            },
            sort=[
                (
                    "created_at",
                    -1,
                ),
            ],
        )

        if document is None:
            return None

        created_at = normalize_created_at(
            document.get(
                "created_at"
            )
        )

        if created_at is None:
            return None

        return created_at.isoformat()

    except Exception as e:
        logger.exception(
            "Archive Viewer failed to find "
            "latest Snapshot: "
            f"url={url}, "
            f"error={e}"
        )

        raise


def find_snapshot(
    url: str,
    created_at: datetime,
) -> dict[str, Any] | None:
    """
    查詢指定 Snapshot。

    Snapshot Identity：

        URL
        +
        created_at
    """

    collection = get_mongo_collection()

    normalized_created_at = normalize_created_at(
        created_at
    )

    if normalized_created_at is None:
        return None

    query = {
        "url": url,
        "created_at": normalized_created_at,
    }

    try:
        document = collection.find_one(
            query
        )

        if document is None:
            logger.warning(
                "Archive Viewer Snapshot not found: "
                f"url={url}, "
                f"created_at={normalized_created_at}"
            )

            return None

        return document

    except Exception as e:
        logger.exception(
            "Archive Viewer Snapshot lookup failed: "
            f"url={url}, "
            f"created_at={normalized_created_at}, "
            f"error={e}"
        )

        raise


def extract_html(
    snapshot: dict[str, Any] | None,
) -> str | None:

    if not snapshot:
        return None

    html = snapshot.get(
        "html"
    )

    if isinstance(
        html,
        str,
    ) and html:
        return html

    raw_html = snapshot.get(
        "raw_html"
    )

    if isinstance(
        raw_html,
        str,
    ) and raw_html:
        return raw_html

    content = snapshot.get(
        "content"
    )

    if isinstance(
        content,
        str,
    ) and content:
        return content

    return None


def build_snapshot_metadata(
    snapshot: dict[str, Any] | None,
) -> dict[str, Any]:

    if not snapshot:
        return {
            "mongo_id": None,
            "document_id": None,
            "content_hash": None,
            "resolved_url": None,
            "created_at": None,
        }

    mongo_id = snapshot.get(
        "_id"
    )

    created_at = normalize_created_at(
        snapshot.get(
            "created_at"
        )
    )

    return {
        "mongo_id":
            str(mongo_id)
            if mongo_id is not None
            else None,

        "document_id":
            snapshot.get(
                "document_id"
            ),

        "content_hash":
            snapshot.get(
                "content_hash"
            ),

        "resolved_url":
            snapshot.get(
                "resolved_url"
            ),

        "created_at":
            created_at.isoformat()
            if created_at is not None
            else None,
    }


def get_snapshot_resources(
    snapshot: dict[str, Any] | None,
) -> dict[str, list]:

    if not snapshot:
        return {
            "css": [],
            "images": [],
        }

    resources = snapshot.get(
        "resources"
    )

    if not isinstance(
        resources,
        dict,
    ):
        return {
            "css": [],
            "images": [],
        }

    css = resources.get(
        "css"
    )

    images = resources.get(
        "images"
    )

    if not isinstance(
        css,
        list,
    ):
        css = []

    if not isinstance(
        images,
        list,
    ):
        images = []

    return {
        "css": css,
        "images": images,
    }


def normalize_resource_url(
    resource_url: Any,
) -> str | None:

    if resource_url is None:
        return None

    if not isinstance(
        resource_url,
        str,
    ):
        return None

    resource_url = resource_url.strip()

    if not resource_url:
        return None

    return resource_url


def resolve_resource_url(
    resource_url: str,
    original_url: str,
) -> str:

    if not resource_url:
        return resource_url

    return urljoin(
        original_url,
        resource_url,
    )


def find_css_resource(
    snapshot: dict[str, Any],
    resource_url: str,
    original_url: str,
) -> dict[str, Any] | None:

    resources = get_snapshot_resources(
        snapshot
    )

    requested_url = resolve_resource_url(
        resource_url,
        original_url,
    )

    for resource in resources["css"]:
        if not isinstance(
            resource,
            dict,
        ):
            continue

        stored_url = normalize_resource_url(
            resource.get(
                "url"
            )
        )

        if not stored_url:
            continue

        absolute_stored_url = resolve_resource_url(
            stored_url,
            original_url,
        )

        if (
            absolute_stored_url
            == requested_url
        ):
            return resource

        if stored_url == resource_url:
            return resource

    return None


def find_image_resource(
    snapshot: dict[str, Any],
    resource_url: str,
    original_url: str,
) -> dict[str, Any] | None:

    resources = get_snapshot_resources(
        snapshot
    )

    requested_url = resolve_resource_url(
        resource_url,
        original_url,
    )

    for resource in resources["images"]:
        if not isinstance(
            resource,
            dict,
        ):
            continue

        stored_url = normalize_resource_url(
            resource.get(
                "url"
            )
        )

        if not stored_url:
            continue

        absolute_stored_url = resolve_resource_url(
            stored_url,
            original_url,
        )

        if (
            absolute_stored_url
            == requested_url
        ):
            return resource

        if stored_url == resource_url:
            return resource

    return None


def encode_resource_identifier(
    resource_url: str,
) -> str:

    return quote(
        resource_url,
        safe="",
    )


def decode_resource_identifier(
    resource_url: str,
) -> str:

    return unquote(
        resource_url
    )


def extract_css_content(
    resource: dict[str, Any] | None,
) -> str | bytes | None:

    if not resource:
        return None

    content = resource.get(
        "content"
    )

    if isinstance(
        content,
        (
            str,
            bytes,
        ),
    ):
        return content

    return None


def extract_image_data(
    resource: dict[str, Any] | None,
) -> bytes | str | None:

    if not resource:
        return None

    data = resource.get(
        "data"
    )

    if isinstance(
        data,
        (
            bytes,
            str,
        ),
    ):
        return data

    return None


def should_rewrite_archive_link(
    href: str,
) -> bool:
    """
    判斷 HTML Link 是否需要改成
    Archive Viewer。

    不改寫：

        #anchor
        mailto:
        tel:
        javascript:
        data:
        blob:
        /archive/...
    """

    if not href:
        return False

    value = href.strip()

    if not value:
        return False

    if value.startswith(
        "/archive/"
    ):
        return False

    if value.startswith(
        "#"
    ):
        return False

    lowered = value.lower()

    excluded_schemes = (
        "mailto:",
        "tel:",
        "javascript:",
        "data:",
        "blob:",
    )

    if lowered.startswith(
        excluded_schemes
    ):
        return False

    return True


def force_new_tab(
    attrs: str,
) -> str:
    """
    確保 Anchor：

        target="_blank"
        rel="noopener noreferrer"

    如果原本存在 target / rel，
    直接移除後重新加入。

    這樣可以避免：

        target="_self"

    或其他舊 target 造成 Archive Viewer
    沒有開啟新分頁。
    """

    attrs = re.sub(
        r"""\s+\btarget\s*=\s*(?:"[^"]*"|'[^']*')""",
        "",
        attrs,
        flags=re.IGNORECASE,
    )

    attrs = re.sub(
        r"""\s+\brel\s*=\s*(?:"[^"]*"|'[^']*')""",
        "",
        attrs,
        flags=re.IGNORECASE,
    )

    return (
        attrs.rstrip()
        + ' target="_blank"'
        + ' rel="noopener noreferrer"'
    )


def rewrite_archive_links(
    html: str,
    original_url: str,
    archive_base_url: str,
) -> str:
    """
    將 Snapshot HTML 中的 HTTP/HTTPS/相對 Link
    動態改寫成 Archive Viewer URL。

    行為：

        Article Link
            ↓
        http://127.0.0.1:8000/archive/view?url=...

        並使用：

            target="_blank"

        開啟新的 Archive Viewer 分頁。

    MongoDB 原始 HTML 不修改。
    """

    if not html:
        return html

    if not original_url:
        return html

    anchor_pattern = re.compile(
        r"""<a\b(?P<attrs>(?:[^>"']|"[^"]*"|'[^']*')*)>""",
        re.IGNORECASE | re.DOTALL,
    )

    href_pattern = re.compile(
        r"""\bhref\s*=\s*(["'])(.*?)\1""",
        re.IGNORECASE | re.DOTALL,
    )

    def replace_anchor(
        match: re.Match,
    ) -> str:

        attrs = match.group(
            "attrs"
        )

        href_match = href_pattern.search(
            attrs
        )

        if href_match is None:
            return match.group(
                0
            )

        raw_href = href_match.group(
            2
        )

        href = unescape(
            raw_href
        ).strip()

        if not should_rewrite_archive_link(
            href
        ):
            return match.group(
                0
            )

        absolute_url = urljoin(
            original_url,
            href,
        )

        if not absolute_url:
            return match.group(
                0
            )

        parsed = urlsplit(
            absolute_url
        )

        if parsed.scheme.lower() not in (
            "http",
            "https",
        ):
            return match.group(
                0
            )

        archive_target_url = parsed._replace(
            fragment=""
        ).geturl()

        archive_link = build_archive_view_url(
            archive_target_url,
            archive_base_url,
        )

        escaped_archive_link = escape(
            archive_link,
            quote=True,
        )

        new_attrs = (
            attrs[
                :href_match.start(2)
            ]
            + escaped_archive_link
            + attrs[
                href_match.end(2):
            ]
        )

        new_attrs = force_new_tab(
            new_attrs
        )

        rewritten_tag = (
            "<a"
            + new_attrs
            + ">"
        )

        return rewritten_tag

    rewritten_html = anchor_pattern.sub(
        replace_anchor,
        html,
    )

    logger.info(
        "Archive Viewer rewritten HTML links: "
        f"original_url={original_url}, "
        f"archive_base_url={archive_base_url}, "
        f"html_length={len(rewritten_html)}"
    )

    return rewritten_html


def prepare_snapshot_html(
    html: str,
    original_url: str,
    snapshot: dict[str, Any],
    snapshot_version: str,
    archive_base_url: str,
) -> str:

    if not html:
        return html

    if not original_url:
        return html

    resources = get_snapshot_resources(
        snapshot
    )

    css_resources = resources[
        "css"
    ]

    image_resources = resources[
        "images"
    ]

    rewritten_html = html

    for resource in css_resources:
        if not isinstance(
            resource,
            dict,
        ):
            continue

        resource_url = normalize_resource_url(
            resource.get(
                "url"
            )
        )

        if not resource_url:
            continue

        absolute_url = resolve_resource_url(
            resource_url,
            original_url,
        )

        encoded_url = encode_resource_identifier(
            resource_url
        )

        archive_css_url = (
            archive_base_url.rstrip("/")
            + "/archive/resource/css/"
            + encoded_url
            + "?url="
            + quote(
                original_url,
                safe="",
            )
            + "&version="
            + quote(
                snapshot_version,
                safe="",
            )
        )

        rewritten_html = rewritten_html.replace(
            absolute_url,
            archive_css_url,
        )

        rewritten_html = rewritten_html.replace(
            resource_url,
            archive_css_url,
        )

    for resource in image_resources:
        if not isinstance(
            resource,
            dict,
        ):
            continue

        resource_url = normalize_resource_url(
            resource.get(
                "url"
            )
        )

        if not resource_url:
            continue

        absolute_url = resolve_resource_url(
            resource_url,
            original_url,
        )

        encoded_url = encode_resource_identifier(
            resource_url
        )

        archive_image_url = (
            archive_base_url.rstrip("/")
            + "/archive/resource/image/"
            + encoded_url
            + "?url="
            + quote(
                original_url,
                safe="",
            )
            + "&version="
            + quote(
                snapshot_version,
                safe="",
            )
        )

        rewritten_html = rewritten_html.replace(
            absolute_url,
            archive_image_url,
        )

        rewritten_html = rewritten_html.replace(
            resource_url,
            archive_image_url,
        )

    rewritten_html = rewrite_archive_links(
        rewritten_html,
        original_url,
        archive_base_url,
    )

    safe_base_url = escape(
        original_url,
        quote=True,
    )

    base_tag = (
        f'<base href="{safe_base_url}">'
    )

    lower_html = rewritten_html.lower()

    if "<base " not in lower_html:
        head_start = lower_html.find(
            "<head"
        )

        if head_start != -1:
            head_end = rewritten_html.find(
                ">",
                head_start,
            )

            if head_end != -1:
                rewritten_html = (
                    rewritten_html[
                        :head_end + 1
                    ]
                    + "\n"
                    + base_tag
                    + "\n"
                    + rewritten_html[
                        head_end + 1:
                    ]
                )

        else:
            rewritten_html = (
                "<head>\n"
                + base_tag
                + "\n</head>\n"
                + rewritten_html
            )

    logger.info(
        "Archive Viewer prepared snapshot HTML: "
        f"original_url={original_url}, "
        f"archive_base_url={archive_base_url}, "
        f"css_resources={len(css_resources)}, "
        f"image_resources={len(image_resources)}, "
        f"html_length={len(rewritten_html)}"
    )

    return rewritten_html


@router.get(
    "/link",
    include_in_schema=False,
)
def archive_link(
    url: str = Query(
        ...,
        min_length=1,
        description="Target URL from archived HTML.",
    ),
):
    """
    舊版 Archive Link Router。

    注意：

        新的 Archived HTML 不再使用此 Router。

    保留此 Route 是為了避免既有舊連結直接失效。
    """

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid archive link URL.",
        )

    parsed_url = urlsplit(
        normalized_url
    )

    if parsed_url.scheme.lower() not in (
        "http",
        "https",
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Archive link only supports "
                "HTTP and HTTPS URLs."
            ),
        )

    lookup_url = parsed_url._replace(
        fragment=""
    ).geturl()

    try:
        latest_version = find_latest_snapshot_version(
            lookup_url
        )

    except Exception:
        logger.exception(
            "Archive Link Snapshot lookup failed: "
            f"url={lookup_url}"
        )

        return RedirectResponse(
            url=normalized_url,
            status_code=307,
        )

    if latest_version is not None:
        archive_snapshot_url = (
            "/archive/snapshot"
            "?url="
            + quote(
                lookup_url,
                safe="",
            )
            + "&version="
            + quote(
                latest_version,
                safe="",
            )
        )

        if parsed_url.fragment:
            archive_snapshot_url += (
                "#"
                + parsed_url.fragment
            )

        logger.info(
            "Archive Link redirected to Snapshot: "
            f"url={lookup_url}, "
            f"version={latest_version}"
        )

        return RedirectResponse(
            url=archive_snapshot_url,
            status_code=307,
        )

    logger.info(
        "Archive Link no Snapshot, "
        "redirecting to original URL: "
        f"url={normalized_url}"
    )

    return RedirectResponse(
        url=normalized_url,
        status_code=307,
    )


@router.get(
    "/view",
    include_in_schema=False,
)
def archive_view(
    request: Request,
    url: str = Query(
        ...,
        min_length=1,
        description="Original article URL.",
    ),
    version: str | None = Query(
        None,
        description=(
            "Snapshot created_at in ISO 8601 format. "
            "If omitted, only Snapshot History is loaded."
        ),
    ),
):
    """
    Archive Article Viewer UI。

    初次：

        /archive/view?url=...

    只顯示 Snapshot History。

    選擇版本後：

        /archive/view?
            url=...
            &version=...

    Viewer iframe：

        /archive/snapshot?
            url=...
            &version=...
    """

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid archive article URL.",
        )

    requested_created_at = None

    if version is not None:
        requested_created_at = normalize_created_at(
            version
        )

        if requested_created_at is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid archive version. "
                    "Version must be a valid "
                    "ISO 8601 created_at datetime."
                ),
            )

    archive_base_url = get_archive_base_url(
        request
    )

    try:
        versions = find_snapshot_history(
            normalized_url
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to query Archive "
                "Snapshot History."
            ),
        )

    for item in versions:
        version_value = item.get(
            "version"
        )

        if version_value:
            item[
                "view_url"
            ] = build_archive_view_url(
                normalized_url,
                archive_base_url,
                version_value,
            )

        else:
            item[
                "view_url"
            ] = None

    if requested_created_at is None:
        logger.info(
            "Archive Viewer initial view: "
            f"url={normalized_url}, "
            f"versions={len(versions)}, "
            "html=False"
        )

        return templates.TemplateResponse(
            request=request,
            name="archive/viewer.html",
            context={
                "title":
                    "Article Archive",

                "url":
                    normalized_url,

                "versions":
                    versions,

                "selected_version":
                    None,

                "selected_created_at":
                    None,

                "snapshot_url":
                    None,

                "html":
                    None,

                "mongo_id":
                    None,

                "document_id":
                    None,

                "content_hash":
                    None,

                "resolved_url":
                    None,
            },
        )

    requested_version = (
        requested_created_at.isoformat()
    )

    selected_version = None

    for item in versions:
        if (
            item.get(
                "version"
            )
            == requested_version
        ):
            selected_version = item
            break

    if selected_version is None:
        logger.warning(
            "Archive Viewer requested version "
            "does not exist: "
            f"url={normalized_url}, "
            f"version={requested_version}"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Archive snapshot version not found."
            ),
        )

    snapshot_url = build_archive_snapshot_url(
        normalized_url,
        requested_version,
        archive_base_url,
    )

    logger.info(
        "Archive Viewer selected snapshot UI: "
        f"url={normalized_url}, "
        f"version={requested_version}, "
        f"snapshot_url={snapshot_url}"
    )

    return templates.TemplateResponse(
        request=request,
        name="archive/viewer.html",
        context={
            "title":
                "Article Archive",

            "url":
                normalized_url,

            "versions":
                versions,

            "selected_version":
                selected_version.get(
                    "version"
                ),

            "selected_created_at":
                selected_version.get(
                    "created_at"
                ),

            "snapshot_url":
                snapshot_url,

            "html":
                None,

            "mongo_id":
                None,

            "document_id":
                None,

            "content_hash":
                None,

            "resolved_url":
                normalized_url,
        },
    )


@router.get(
    "/snapshot",
    include_in_schema=False,
)
def archive_snapshot(
    request: Request,
    url: str = Query(
        ...,
        min_length=1,
        description="Original article URL.",
    ),
    version: str = Query(
        ...,
        description=(
            "Snapshot created_at in ISO 8601 format."
        ),
    ),
):

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid archive article URL.",
        )

    requested_created_at = normalize_created_at(
        version
    )

    if requested_created_at is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid archive version. "
                "Version must be a valid "
                "ISO 8601 created_at datetime."
            ),
        )

    try:
        snapshot = find_snapshot(
            normalized_url,
            requested_created_at,
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to query Archive Snapshot."
            ),
        )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Archive snapshot not found."
            ),
        )

    html = extract_html(
        snapshot
    )

    if html is None:
        logger.warning(
            "Archive Snapshot has no HTML: "
            f"url={normalized_url}, "
            f"version={requested_created_at.isoformat()}"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Snapshot HTML not found."
            ),
        )

    original_url = (
        snapshot.get(
            "resolved_url"
        )
        or snapshot.get(
            "url"
        )
        or normalized_url
    )

    original_url = str(
        original_url
    ).strip()

    snapshot_version = (
        requested_created_at.isoformat()
    )

    archive_base_url = get_archive_base_url(
        request
    )

    prepared_html = prepare_snapshot_html(
        html,
        original_url,
        snapshot,
        snapshot_version,
        archive_base_url,
    )

    resources = get_snapshot_resources(
        snapshot
    )

    logger.info(
        "Archive Snapshot HTML served: "
        f"url={normalized_url}, "
        f"version={snapshot_version}, "
        f"original_url={original_url}, "
        f"archive_base_url={archive_base_url}, "
        f"html_length={len(prepared_html)}, "
        f"css_resources={len(resources['css'])}, "
        f"image_resources={len(resources['images'])}"
    )

    return Response(
        content=prepared_html,
        media_type="text/html",
        headers={
            "Content-Disposition": "inline",
            "X-Archive-Snapshot": "true",
        },
    )


@router.get(
    "/resource/css/{resource_url:path}",
    include_in_schema=False,
)
def archive_css_resource(
    resource_url: str,
    url: str = Query(
        ...,
        min_length=1,
        description="Original article URL.",
    ),
    version: str = Query(
        ...,
        description=(
            "Snapshot created_at in ISO 8601 format."
        ),
    ),
):

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid archive article URL.",
        )

    requested_created_at = normalize_created_at(
        version
    )

    if requested_created_at is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid archive version."
            ),
        )

    decoded_resource_url = (
        decode_resource_identifier(
            resource_url
        )
    )

    try:
        snapshot = find_snapshot(
            normalized_url,
            requested_created_at,
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to query Archive Snapshot."
            ),
        )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Archive snapshot not found."
            ),
        )

    original_url = (
        snapshot.get(
            "resolved_url"
        )
        or snapshot.get(
            "url"
        )
        or normalized_url
    )

    original_url = str(
        original_url
    ).strip()

    css_resource = find_css_resource(
        snapshot,
        decoded_resource_url,
        original_url,
    )

    if css_resource is None:
        logger.warning(
            "Archive CSS resource not found: "
            f"url={normalized_url}, "
            f"version={requested_created_at.isoformat()}, "
            f"resource={decoded_resource_url}"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Archive CSS resource not found."
            ),
        )

    css_content = extract_css_content(
        css_resource
    )

    if css_content is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Archive CSS content not found."
            ),
        )

    mime_type = (
        css_resource.get(
            "mime_type"
        )
        or "text/css"
    )

    mime_type = str(
        mime_type
    )

    logger.info(
        "Archive CSS resource served: "
        f"url={normalized_url}, "
        f"version={requested_created_at.isoformat()}, "
        f"resource={decoded_resource_url}"
    )

    return Response(
        content=css_content,
        media_type=mime_type,
        headers={
            "Content-Disposition": "inline",
            "X-Archive-Resource": "css",
        },
    )


@router.get(
    "/resource/image/{resource_url:path}",
    include_in_schema=False,
)
def archive_image_resource(
    resource_url: str,
    url: str = Query(
        ...,
        min_length=1,
        description="Original article URL.",
    ),
    version: str = Query(
        ...,
        description=(
            "Snapshot created_at in ISO 8601 format."
        ),
    ),
):

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        raise HTTPException(
            status_code=400,
            detail="Invalid archive article URL.",
        )

    requested_created_at = normalize_created_at(
        version
    )

    if requested_created_at is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid archive version."
            ),
        )

    decoded_resource_url = (
        decode_resource_identifier(
            resource_url
        )
    )

    try:
        snapshot = find_snapshot(
            normalized_url,
            requested_created_at,
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to query Archive Snapshot."
            ),
        )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Archive snapshot not found."
            ),
        )

    original_url = (
        snapshot.get(
            "resolved_url"
        )
        or snapshot.get(
            "url"
        )
        or normalized_url
    )

    original_url = str(
        original_url
    ).strip()

    image_resource = find_image_resource(
        snapshot,
        decoded_resource_url,
        original_url,
    )

    if image_resource is None:
        logger.warning(
            "Archive Image resource not found: "
            f"url={normalized_url}, "
            f"version={requested_created_at.isoformat()}, "
            f"resource={decoded_resource_url}"
        )

        raise HTTPException(
            status_code=404,
            detail=(
                "Archive Image resource not found."
            ),
        )

    image_data = extract_image_data(
        image_resource
    )

    if image_data is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Archive Image data not found."
            ),
        )

    mime_type = (
        image_resource.get(
            "mime_type"
        )
        or "application/octet-stream"
    )

    mime_type = str(
        mime_type
    )

    logger.info(
        "Archive Image resource served: "
        f"url={normalized_url}, "
        f"version={requested_created_at.isoformat()}, "
        f"resource={decoded_resource_url}, "
        f"mime_type={mime_type}"
    )

    return Response(
        content=image_data,
        media_type=mime_type,
        headers={
            "Content-Disposition": "inline",
            "X-Archive-Resource": "image",
        },
    )


__all__ = [
    "router",
]