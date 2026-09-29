"""
parser/parser.py

AutoSearch V5

V5 Parser

用途：

1. HTML 解析
2. 移除 HTML 結構垃圾
3. 移除廣告 / 推薦區塊
4. Content Density Score
5. Keyword Ranking
6. 找真正文章正文
7. 支援中文 / 英文新聞
8. 傳給 Cleaner / Extractor 清理
9. 建立 Article Object
10. 建立完整文章內容 SHA-256 Hash 作為 document_id

Fallback Strategy：

    正常 Main Content Detection
            ↓
    找不到可靠正文
            ↓
    Largest Text Block Fallback
            ↓
    找頁面中「文字最多」的合理區塊
            ↓
    Cleaner
            ↓
    Extractor
            ↓
    Article

Pipeline：

    Crawler
        ↓
    HTML
        ↓
    Parser
        ↓
    Clean / Extract
        ↓
    Article
        ↓
    ArticleRepository
        ↓
    SQL
        ↓
    AI Task / Archive
"""

from hashlib import sha256

from bs4 import BeautifulSoup

from cleaner.cleaner import (
    clean_text,
)

from extractor.extractor import (
    extract,
)

from models.article import (
    Article,
)


BAD_WORDS = [
    "advert",
    "advertisement",
    "ad-banner",
    "ad-container",
    "ads-container",
    "advertising",
    "sponsor",
    "sponsored",
    "related-news",
    "related-article",
    "related-content",
    "recommended",
    "recommendation",
    "more-news",
    "latest-news",
    "you-may-like",
    "social-share",
    "social-links",
    "share-buttons",
    "share-tools",
    "subscribe",
    "newsletter",
    "login",
    "register",
    "breadcrumb",
    "navigation",
    "navbar",
    "menu",
]


def generate_document_id(
    content,
):
    """
    根據完整文章正文建立 document_id。

    document_id =
        SHA-256(
            完整清理後文章正文
        )
    """

    if content is None:
        raise ValueError(
            "generate_document_id() "
            "requires content"
        )

    if not isinstance(
        content,
        str,
    ):
        content = str(
            content
        )

    content = content.strip()

    if not content:
        raise ValueError(
            "generate_document_id() "
            "requires non-empty content"
        )

    return sha256(
        content.encode(
            "utf-8"
        )
    ).hexdigest()


def remove_html_noise(
    soup,
):
    """
    移除常見 HTML 噪音。

    包含：

        - script
        - style
        - nav
        - header
        - footer
        - aside
        - form
        - iframe
        - button

    以及 class / id 中常見的廣告、推薦、
    社群、會員與導覽區塊。
    """

    if soup is None:
        return soup

    remove_tags = [
        "script",
        "style",
        "noscript",
        "nav",
        "header",
        "footer",
        "aside",
        "form",
        "iframe",
        "button",
    ]

    for tag_name in remove_tags:
        for tag in soup.find_all(
            tag_name
        ):
            try:
                tag.decompose()
            except Exception:
                pass

    nodes = list(
        soup.find_all(True)
    )

    for node in nodes:
        if not getattr(
            node,
            "attrs",
            None,
        ):
            continue

        classes = node.get(
            "class",
            [],
        )

        if isinstance(
            classes,
            list,
        ):
            classes = " ".join(
                str(item)
                for item in classes
            )
        else:
            classes = str(
                classes
            )

        node_id = node.get(
            "id",
            "",
        )

        attributes = (
            f"{classes} "
            f"{node_id}"
        ).lower()

        should_remove = False

        for word in BAD_WORDS:
            if word in attributes:
                should_remove = True
                break

        if should_remove:
            try:
                node.decompose()
            except AttributeError:
                pass

    return soup


def get_node_text(
    node,
):
    """
    取得候選節點的純文字。

    使用統一 separator，避免不同網站的 HTML
    結構導致文字全部黏在一起。
    """

    if node is None:
        return ""

    try:
        text = node.get_text(
            separator="\n",
            strip=True,
        )
    except Exception:
        return ""

    if not isinstance(
        text,
        str,
    ):
        text = str(
            text
        )

    return text.strip()


def text_length(
    node,
):
    """
    計算候選節點的有效文字長度。
    """

    return len(
        get_node_text(
            node
        )
    )


def content_score(
    node,
    keyword="",
):
    """
    計算候選節點的正文分數。

    評估：

        - Text Length
        - Link Penalty
        - HTML Complexity
        - Content Density
        - Keyword Bonus

    分數越高，越可能是真正文章正文。

    如果沒有任何節點得到可靠分數，
    find_main_content() 會進入
    largest text block fallback。
    """

    if node is None:
        return 0

    text = get_node_text(
        node
    )

    if len(text) < 100:
        return 0

    text_score = len(
        text
    )

    links = len(
        node.find_all("a")
    )

    link_penalty = (
        links * 35
    )

    tags = len(
        node.find_all()
    )

    tag_penalty = (
        tags * 1.5
    )

    html_size = len(
        str(node)
    )

    density = (
        len(text)
        /
        (html_size + 1)
    )

    density_bonus = (
        density * 500
    )

    keyword_bonus = 0

    if keyword:
        keyword_text = str(
            keyword
        ).strip()

        if keyword_text:
            keyword_count = (
                text.lower().count(
                    keyword_text.lower()
                )
            )

            keyword_bonus = (
                keyword_count * 100
            )

    score = (
        text_score
        - link_penalty
        - tag_penalty
        + density_bonus
        + keyword_bonus
    )

    return score


def find_largest_text_block(
    soup,
):
    """
    找出頁面中「文字最多」的合理區塊。

    當網站沒有標準 article 結構或 Content Score
    無法可靠判斷時，搜尋 section / div / td / body，
    選擇文字最多且不是 link-heavy 的合理區塊。
    """

    if soup is None:
        return ""

    candidates = []

    for tag_name in [
        "article",
        "main",
        "section",
        "div",
        "td",
    ]:
        try:
            nodes = soup.find_all(
                tag_name
            )
        except Exception:
            nodes = []

        for node in nodes:
            candidates.append(
                node
            )

    if soup.body is not None:
        candidates.append(
            soup.body
        )

    best_node = None
    best_length = 0
    best_score = 0
    seen_nodes = set()

    for node in candidates:
        node_id = id(
            node
        )

        if node_id in seen_nodes:
            continue

        seen_nodes.add(
            node_id
        )

        text = get_node_text(
            node
        )

        length = len(
            text
        )

        if length < 200:
            continue

        links = len(
            node.find_all("a")
        )

        words = len(
            text.split()
        )

        if words <= 0:
            continue

        link_ratio = (
            links
            /
            max(
                words,
                1,
            )
        )

        if link_ratio > 0.8:
            continue

        score = (
            length
            *
            (
                1
                -
                min(
                    link_ratio,
                    0.7,
                )
                * 0.5
            )
        )

        if score > best_score:
            best_score = score
            best_length = length
            best_node = node

    if best_node is not None:
        return get_node_text(
            best_node
        )

    if soup.body is not None:
        body_text = get_node_text(
            soup.body
        )

        if len(body_text) >= 200:
            return body_text

    return ""


def find_main_content(
    soup,
    keyword="",
):
    """
    找出最可能的文章正文。

    Strategy：

        第一層：
            Article / Main / 常見 Article Selector

        第二層：
            Content Score

        第三層：
            Largest Text Block

        第四層：
            Body Text
    """

    if soup is None:
        return ""

    candidates = []

    for node in soup.find_all(
        "article"
    ):
        candidates.append(
            node
        )

    for node in soup.find_all(
        "main"
    ):
        candidates.append(
            node
        )

    selectors = [
        ".article-body",
        ".article-content",
        ".article-text",
        ".article-detail",
        ".article-detail-content",
        ".post-content",
        ".post-body",
        ".entry-content",
        ".story-body",
        ".story-content",
        ".news-content",
        ".news-body",
        ".content-body",
        ".content-detail",
        ".content-article",
        ".article-main",
        ".article-container",
        "#article-content",
        "#article-body",
        "#article",
        "#content",
        "#main-content",
    ]

    for selector in selectors:
        try:
            nodes = soup.select(
                selector
            )
        except Exception:
            nodes = []

        for node in nodes:
            candidates.append(
                node
            )

    best_node = None
    best_score = 0
    seen_nodes = set()

    for node in candidates:
        node_id = id(
            node
        )

        if node_id in seen_nodes:
            continue

        seen_nodes.add(
            node_id
        )

        score = content_score(
            node,
            keyword,
        )

        if score > best_score:
            best_score = score
            best_node = node

    if best_node is None:
        fallback_candidates = []

        for tag_name in [
            "section",
            "div",
        ]:
            try:
                fallback_candidates.extend(
                    soup.find_all(
                        tag_name
                    )
                )
            except Exception:
                pass

        for node in fallback_candidates:
            score = content_score(
                node,
                keyword,
            )

            if score > best_score:
                best_score = score
                best_node = node

    if best_node is not None:
        content = get_node_text(
            best_node
        )

        if len(content) >= 200:
            return content

    largest_content = (
        find_largest_text_block(
            soup
        )
    )

    if len(largest_content) >= 200:
        return largest_content

    if soup.body is not None:
        body_content = get_node_text(
            soup.body
        )

        if body_content:
            return body_content

    return get_node_text(
        soup
    )


def parse(
    html,
    keyword,
    url="",
):
    """
    解析 HTML 並建立 Article。

    Parser Strategy：

        HTML
          ↓
        Remove Noise
          ↓
        Main Content Detection
          ↓
        Content Score
          ↓
        Largest Text Block Fallback
          ↓
        Body Fallback
          ↓
        Cleaner
          ↓
        Extractor
          ↓
        Article
    """

    if html is None:
        raise ValueError(
            "parse() requires html"
        )

    if isinstance(
        html,
        bytes,
    ):
        try:
            html = html.decode(
                "utf-8",
                errors="replace",
            )
        except Exception as e:
            raise ValueError(
                f"Failed to decode html: {e}"
            ) from e

    elif not isinstance(
        html,
        str,
    ):
        html = str(
            html
        )

    html = html.strip()

    if not html:
        raise ValueError(
            "parse() requires non-empty html"
        )

    if keyword is None:
        raise ValueError(
            "parse() requires keyword"
        )

    keyword = str(
        keyword
    ).strip()

    if not keyword:
        raise ValueError(
            "parse() requires non-empty keyword"
        )

    if url is None:
        url = ""

    url = str(
        url
    ).strip()

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    soup = remove_html_noise(
        soup
    )

    content = find_main_content(
        soup,
        keyword,
    )

    if not content:
        content = get_node_text(
            soup.body
            if soup.body is not None
            else soup
        )

    content = clean_text(
        content
    )

    content = extract(
        content
    )

    if content is None:
        content = ""

    if not isinstance(
        content,
        str,
    ):
        content = str(
            content
        )

    content = content.strip()

    if not content:
        fallback_content = find_main_content(
            BeautifulSoup(
                html,
                "html.parser",
            ),
            keyword,
        )

        fallback_content = clean_text(
            fallback_content
        )

        if fallback_content:
            content = fallback_content.strip()

    if not content:
        raise ValueError(
            "parse() produced empty article content"
        )

    document_id = generate_document_id(
        content
    )

    article = Article()

    if soup.title:
        article.title = (
            soup.title.get_text(
                strip=True
            )
        )
    else:
        article.title = ""

    article.url = url
    article.published = None
    article.keyword = keyword
    article.content = content
    article.document_id = (
        document_id
    )

    return article


__all__ = [
    "generate_document_id",
    "remove_html_noise",
    "get_node_text",
    "text_length",
    "content_score",
    "find_largest_text_block",
    "find_main_content",
    "parse",
]