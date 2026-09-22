"""
site_profile.py

AutoSearch V7

R2 Site Profile

輸入一個 URL，自動完成：

1. Site Identity
2. HTML Strategy Probe
3. HTML Best Strategy Selection
4. 使用 HTML Best Strategy 取得 HTML
5. CSS / Image Discovery
6. CSS Strategy Probe
7. Image 隨機抽取最多 2 個 URL
8. Image Strategy Probe
9. Strategy Evaluation
10. Best Strategy Selection

最終只保存：

    HTML → Best Strategy
    CSS  → Best Strategy
    Image → Best Strategy

Probe 結果只存在記憶體。

Evaluation：

    Content Size 優先
    Content Size 相同時 Speed 優先
"""

from __future__ import annotations

import random
import time

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from crawler.retrieval.html_retrieval import (
    get_html_retrieval_strategies,
)
from crawler.retrieval.css_retrieval import (
    get_css_retrieval_strategies,
)
from crawler.retrieval.image_retrieval import (
    get_image_retrieval_strategies,
)


@dataclass
class SiteIdentity:
    hostname: str
    scheme: str
    base_url: str


@dataclass
class StrategyEvaluation:
    strategy: str
    success: bool
    completeness: float
    content_size: int
    elapsed_time: float


@dataclass
class SiteProfile:
    site: SiteIdentity
    html_best_strategy: Optional[str] = None
    css_best_strategy: Optional[str] = None
    image_best_strategy: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site": {
                "hostname": self.site.hostname,
                "scheme": self.site.scheme,
                "base_url": self.site.base_url,
            },
            "html": {
                "best_strategy": self.html_best_strategy,
            },
            "css": {
                "best_strategy": self.css_best_strategy,
            },
            "image": {
                "best_strategy": self.image_best_strategy,
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class _ResourceHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()

        self.css_urls: List[str] = []
        self.image_urls: List[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:
        attributes = dict(attrs)
        tag = tag.lower()

        if tag == "link":
            rel = attributes.get("rel", "")
            href = attributes.get("href")

            rel_values = {
                value.strip().lower()
                for value in rel.split()
            }

            if (
                href
                and "stylesheet" in rel_values
            ):
                self.css_urls.append(href)

        elif tag == "img":
            src = attributes.get("src")

            if src:
                self.image_urls.append(src)

        elif tag == "source":
            src = attributes.get("src")

            if src:
                self.image_urls.append(src)


def build_site_identity(
    url: str,
) -> SiteIdentity:
    parsed = urlparse(url)

    scheme = (
        parsed.scheme
        or ""
    ).lower()

    hostname = (
        parsed.hostname
        or ""
    ).lower()

    if not scheme:
        raise ValueError(
            "URL scheme is required"
        )

    if not hostname:
        raise ValueError(
            "URL hostname is required"
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(
            f"Invalid URL port: {exc}"
        ) from exc

    if port is not None:
        host = f"{hostname}:{port}"
    else:
        host = hostname

    base_url = f"{scheme}://{host}/"

    return SiteIdentity(
        hostname=hostname,
        scheme=scheme,
        base_url=base_url,
    )


def _get_result_value(
    result: Any,
    name: str,
    default: Any = None,
) -> Any:
    if hasattr(result, name):
        return getattr(
            result,
            name,
        )

    if isinstance(result, dict):
        return result.get(
            name,
            default,
        )

    return default


def _get_content_size(
    result: Any,
) -> int:
    content_size = _get_result_value(
        result,
        "content_size",
        0,
    )

    try:
        content_size = int(
            content_size
        )
    except (
        TypeError,
        ValueError,
    ):
        content_size = 0

    return max(
        content_size,
        0,
    )


def _calculate_completeness(
    result: Any,
) -> float:
    success = bool(
        _get_result_value(
            result,
            "success",
            False,
        )
    )

    if not success:
        return 0.0

    content_size = _get_content_size(
        result
    )

    if content_size <= 0:
        return 0.0

    return float(
        content_size
    )


def _decode_content(
    content: Any,
) -> Optional[str]:
    if content is None:
        return None

    if isinstance(content, bytes):
        for encoding in (
            "utf-8",
            "utf-8-sig",
            "big5",
            "cp950",
            "latin-1",
        ):
            try:
                return content.decode(
                    encoding
                )
            except UnicodeDecodeError:
                continue

        return content.decode(
            "utf-8",
            errors="replace",
        )

    if isinstance(content, str):
        return content

    return str(content)


def _get_result_content(
    result: Any,
) -> Optional[str]:
    content = _get_result_value(
        result,
        "content",
        None,
    )

    if content is not None:
        return _decode_content(
            content
        )

    html = _get_result_value(
        result,
        "html",
        None,
    )

    if html is not None:
        return _decode_content(
            html
        )

    return None


def _probe_strategy(
    *,
    strategy_name: str,
    strategy_function,
    url: str,
) -> StrategyEvaluation:
    start_time = time.perf_counter()

    try:
        result = strategy_function(
            url
        )

        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        result_elapsed_time = (
            _get_result_value(
                result,
                "elapsed_time",
                elapsed_time,
            )
        )

        try:
            result_elapsed_time = float(
                result_elapsed_time
            )
        except (
            TypeError,
            ValueError,
        ):
            result_elapsed_time = (
                elapsed_time
            )

        success = bool(
            _get_result_value(
                result,
                "success",
                False,
            )
        )

        content_size = (
            _get_content_size(
                result
            )
        )

        completeness = (
            _calculate_completeness(
                result
            )
        )

        return StrategyEvaluation(
            strategy=strategy_name,
            success=success,
            completeness=completeness,
            content_size=content_size,
            elapsed_time=result_elapsed_time,
        )

    except Exception:
        elapsed_time = (
            time.perf_counter()
            - start_time
        )

        return StrategyEvaluation(
            strategy=strategy_name,
            success=False,
            completeness=0.0,
            content_size=0,
            elapsed_time=elapsed_time,
        )


def probe_strategies(
    url: str,
    strategies: Dict[str, Any],
) -> Dict[str, StrategyEvaluation]:
    results: Dict[
        str,
        StrategyEvaluation,
    ] = {}

    for (
        strategy_name,
        strategy_function,
    ) in strategies.items():

        results[strategy_name] = (
            _probe_strategy(
                strategy_name=strategy_name,
                strategy_function=strategy_function,
                url=url,
            )
        )

    return results


def evaluate_strategy(
    result: StrategyEvaluation,
) -> tuple[float, float]:
    return (
        result.completeness,
        -result.elapsed_time,
    )


def select_best_strategy(
    results: Dict[str, StrategyEvaluation],
) -> Optional[str]:
    successful_results = [
        result
        for result in results.values()
        if result.success
        and result.content_size > 0
    ]

    if not successful_results:
        return None

    best_result = max(
        successful_results,
        key=evaluate_strategy,
    )

    return best_result.strategy


def _probe_html_with_content(
    url: str,
) -> tuple[
    Optional[str],
    Optional[str],
]:
    strategies = (
        get_html_retrieval_strategies()
    )

    evaluations: Dict[
        str,
        StrategyEvaluation,
    ] = {}

    contents: Dict[
        str,
        Optional[str],
    ] = {}

    for (
        strategy_name,
        strategy_function,
    ) in strategies.items():

        start_time = time.perf_counter()

        try:
            result = strategy_function(
                url
            )

            elapsed_time = (
                time.perf_counter()
                - start_time
            )

            result_elapsed_time = (
                _get_result_value(
                    result,
                    "elapsed_time",
                    elapsed_time,
                )
            )

            try:
                result_elapsed_time = float(
                    result_elapsed_time
                )
            except (
                TypeError,
                ValueError,
            ):
                result_elapsed_time = (
                    elapsed_time
                )

            success = bool(
                _get_result_value(
                    result,
                    "success",
                    False,
                )
            )

            content_size = (
                _get_content_size(
                    result
                )
            )

            completeness = (
                _calculate_completeness(
                    result
                )
            )

            evaluations[
                strategy_name
            ] = StrategyEvaluation(
                strategy=strategy_name,
                success=success,
                completeness=completeness,
                content_size=content_size,
                elapsed_time=result_elapsed_time,
            )

            contents[
                strategy_name
            ] = _get_result_content(
                result
            )

        except Exception:
            elapsed_time = (
                time.perf_counter()
                - start_time
            )

            evaluations[
                strategy_name
            ] = StrategyEvaluation(
                strategy=strategy_name,
                success=False,
                completeness=0.0,
                content_size=0,
                elapsed_time=elapsed_time,
            )

            contents[
                strategy_name
            ] = None

    best_strategy = select_best_strategy(
        evaluations
    )

    if best_strategy is None:
        return None, None

    return (
        best_strategy,
        contents.get(
            best_strategy
        ),
    )


def _discover_resources(
    html: str,
    base_url: str,
) -> tuple[
    List[str],
    List[str],
]:
    parser = _ResourceHTMLParser()

    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return [], []

    css_urls: List[str] = []
    image_urls: List[str] = []

    for resource_url in parser.css_urls:
        absolute_url = urljoin(
            base_url,
            resource_url,
        )

        if absolute_url not in css_urls:
            css_urls.append(
                absolute_url
            )

    for resource_url in parser.image_urls:
        absolute_url = urljoin(
            base_url,
            resource_url,
        )

        if absolute_url not in image_urls:
            image_urls.append(
                absolute_url
            )

    return (
        css_urls,
        image_urls,
    )


def discover_css_urls(
    html: str,
    base_url: str,
) -> List[str]:
    css_urls, _ = _discover_resources(
        html,
        base_url,
    )

    return css_urls


def discover_image_urls(
    html: str,
    base_url: str,
) -> List[str]:
    _, image_urls = _discover_resources(
        html,
        base_url,
    )

    return image_urls


def _select_css_url(
    css_urls: List[str],
) -> Optional[str]:
    if not css_urls:
        return None

    return css_urls[0]


def _select_image_urls(
    image_urls: List[str],
    sample_size: int = 2,
) -> List[str]:
    if not image_urls:
        return []

    if len(image_urls) <= sample_size:
        return list(image_urls)

    return random.sample(
        image_urls,
        sample_size,
    )


def probe_html(
    url: str,
) -> Optional[str]:
    best_strategy, _ = (
        _probe_html_with_content(
            url
        )
    )

    return best_strategy


def probe_css(
    url: Optional[str],
) -> Optional[str]:
    if not url:
        return None

    strategies = (
        get_css_retrieval_strategies()
    )

    results = probe_strategies(
        url,
        strategies,
    )

    return select_best_strategy(
        results
    )


def probe_image(
    urls: List[str],
) -> Optional[str]:
    if not urls:
        return None

    strategies = (
        get_image_retrieval_strategies()
    )

    strategy_results: Dict[
        str,
        List[StrategyEvaluation],
    ] = {}

    for image_url in urls:
        results = probe_strategies(
            image_url,
            strategies,
        )

        for (
            strategy_name,
            result,
        ) in results.items():

            strategy_results.setdefault(
                strategy_name,
                [],
            ).append(result)

    strategy_scores: Dict[
        str,
        tuple[float, float],
    ] = {}

    for (
        strategy_name,
        results,
    ) in strategy_results.items():

        total_content_size = sum(
            result.content_size
            for result in results
            if result.success
        )

        total_elapsed_time = sum(
            result.elapsed_time
            for result in results
        )

        if total_content_size <= 0:
            continue

        strategy_scores[
            strategy_name
        ] = (
            float(total_content_size),
            -total_elapsed_time,
        )

    if not strategy_scores:
        return None

    return max(
        strategy_scores,
        key=strategy_scores.get,
    )


def create_site_profile(
    url: str,
) -> SiteProfile:
    site = build_site_identity(
        url
    )

    html_best_strategy, html = (
        _probe_html_with_content(
            url
        )
    )

    css_urls: List[str] = []
    image_urls: List[str] = []

    if html:
        css_urls = discover_css_urls(
            html,
            url,
        )

        image_urls = discover_image_urls(
            html,
            url,
        )

    css_url = _select_css_url(
        css_urls
    )

    selected_image_urls = (
        _select_image_urls(
            image_urls,
            sample_size=2,
        )
    )

    css_best_strategy = probe_css(
        css_url
    )

    image_best_strategy = probe_image(
        selected_image_urls
    )

    now = datetime.now(
        timezone.utc
    )

    return SiteProfile(
        site=site,
        html_best_strategy=(
            html_best_strategy
        ),
        css_best_strategy=(
            css_best_strategy
        ),
        image_best_strategy=(
            image_best_strategy
        ),
        created_at=now,
        updated_at=now,
    )


__all__ = [
    "SiteIdentity",
    "StrategyEvaluation",
    "SiteProfile",
    "build_site_identity",
    "discover_css_urls",
    "discover_image_urls",
    "probe_strategies",
    "evaluate_strategy",
    "select_best_strategy",
    "probe_html",
    "probe_css",
    "probe_image",
    "create_site_profile",
]