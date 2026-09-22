"""
test_site_profile.py

AutoSearch V7

R2 Site Profile Test

測試：

1. Site Identity
2. Strategy Registry
3. HTML Strategy Probe
4. HTML Best Strategy
5. HTML Best Content
6. CSS Discovery
7. Image Discovery
8. CSS Strategy Probe
9. Image Strategy Probe
10. Strategy Evaluation
11. Best Strategy Selection
12. Complete Site Profile
"""

from crawler.retrieval.html_retrieval import (
    get_html_retrieval_strategies,
)
from crawler.retrieval.css_retrieval import (
    get_css_retrieval_strategies,
)
from crawler.retrieval.image_retrieval import (
    get_image_retrieval_strategies,
)
from crawler.retrieval.site_profile import (
    StrategyEvaluation,
    build_site_identity,
    create_site_profile,
    discover_css_urls,
    discover_image_urls,
    evaluate_strategy,
    probe_strategies,
    select_best_strategy,
)


TEST_URL = (
    "https://www.digitimes.com.tw/"
    "research/report-category/"
    "?CnlID=3&cat=CSE"
)


def print_result(
    number: int,
    name: str,
    passed: bool,
) -> None:
    status = "PASS" if passed else "FAIL"

    print(
        f"TEST {number:<2} "
        f"{name:<45} "
        f"{status}"
    )


def decode_html(content):
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
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        return content.decode(
            "utf-8",
            errors="replace",
        )

    if isinstance(content, str):
        return content

    return str(content)


def get_result_html(result):
    html = getattr(
        result,
        "html",
        None,
    )

    if html is not None:
        return decode_html(html)

    content = getattr(
        result,
        "content",
        None,
    )

    return decode_html(content)


def get_best_html_content():
    strategies = (
        get_html_retrieval_strategies()
    )

    results = probe_strategies(
        TEST_URL,
        strategies,
    )

    best_strategy = select_best_strategy(
        results
    )

    if best_strategy is None:
        return (
            None,
            None,
            results,
        )

    strategy_function = strategies[
        best_strategy
    ]

    result = strategy_function(
        TEST_URL
    )

    html = getattr(
        result,
        "html",
        None,
    )

    if html is None:
        html = getattr(
            result,
            "content",
            None,
        )

    html = decode_html(html)

    return (
        best_strategy,
        html,
        results,
    )

def test_site_identity() -> bool:
    identity = build_site_identity(
        TEST_URL
    )

    passed = (
        identity.hostname
        == "www.digitimes.com.tw"
        and identity.scheme
        == "https"
        and identity.base_url
        == "https://www.digitimes.com.tw/"
    )

    if passed:
        print(
            f"  hostname: {identity.hostname}"
        )
        print(
            f"  scheme:   {identity.scheme}"
        )
        print(
            f"  base_url: {identity.base_url}"
        )

    return passed


def test_strategy_registry() -> bool:
    html_strategies = (
        get_html_retrieval_strategies()
    )

    css_strategies = (
        get_css_retrieval_strategies()
    )

    image_strategies = (
        get_image_retrieval_strategies()
    )

    passed = (
        len(html_strategies) == 6
        and len(css_strategies) == 6
        and len(image_strategies) == 6
    )

    print(
        f"  HTML strategies:  "
        f"{list(html_strategies.keys())}"
    )

    print(
        f"  CSS strategies:   "
        f"{list(css_strategies.keys())}"
    )

    print(
        f"  Image strategies: "
        f"{list(image_strategies.keys())}"
    )

    return passed


def test_html_probe() -> bool:
    strategies = (
        get_html_retrieval_strategies()
    )

    results = probe_strategies(
        TEST_URL,
        strategies,
    )

    passed = (
        len(results) == 6
    )

    for result in results.values():
        print(
            f"  "
            f"{result.strategy:<16} "
            f"success={str(result.success):<5} "
            f"size={result.content_size:<8} "
            f"time={result.elapsed_time:.3f}s"
        )

    return passed


def test_html_best_strategy() -> bool:
    strategies = (
        get_html_retrieval_strategies()
    )

    results = probe_strategies(
        TEST_URL,
        strategies,
    )

    best_strategy = select_best_strategy(
        results
    )

    passed = (
        best_strategy is not None
        and best_strategy
        in strategies
    )

    print(
        f"  HTML Best Strategy: "
        f"{best_strategy}"
    )

    return passed


def test_html_best_content() -> bool:
    (
        best_strategy,
        html,
        results,
    ) = get_best_html_content()

    if best_strategy is None:
        return False

    if html is None:
        return False

    selected_result = results[
        best_strategy
    ]

    html_size = len(html)

    passed = (
        selected_result.success
        and selected_result.content_size > 0
        and html_size > 0
    )

    print(
        f"  Best Strategy: "
        f"{best_strategy}"
    )

    print(
        f"  Result Size: "
        f"{selected_result.content_size}"
    )

    print(
        f"  HTML Size: "
        f"{html_size}"
    )

    return passed


def test_css_discovery() -> bool:
    (
        best_strategy,
        html,
        _,
    ) = get_best_html_content()

    if best_strategy is None:
        return False

    if html is None:
        return False

    css_urls = discover_css_urls(
        html,
        TEST_URL,
    )

    passed = (
        isinstance(css_urls, list)
        and len(css_urls) > 0
    )

    print(
        f"  HTML Best Strategy: "
        f"{best_strategy}"
    )

    print(
        f"  CSS URL Count: "
        f"{len(css_urls)}"
    )

    for index, url in enumerate(
        css_urls,
        start=1,
    ):
        print(
            f"  CSS[{index}] {url}"
        )

    return passed


def test_image_discovery() -> bool:
    (
        best_strategy,
        html,
        _,
    ) = get_best_html_content()

    if best_strategy is None:
        return False

    if html is None:
        return False

    image_urls = discover_image_urls(
        html,
        TEST_URL,
    )

    passed = (
        isinstance(image_urls, list)
        and len(image_urls) > 0
    )

    print(
        f"  HTML Best Strategy: "
        f"{best_strategy}"
    )

    print(
        f"  Image URL Count: "
        f"{len(image_urls)}"
    )

    for index, url in enumerate(
        image_urls,
        start=1,
    ):
        print(
            f"  Image[{index}] {url}"
        )

    return passed


def test_css_probe() -> bool:
    (
        best_strategy,
        html,
        _,
    ) = get_best_html_content()

    if best_strategy is None:
        return False

    if html is None:
        return False

    css_urls = discover_css_urls(
        html,
        TEST_URL,
    )

    if not css_urls:
        return False

    css_url = css_urls[0]

    print(
        f"  CSS URL: {css_url}"
    )

    strategies = (
        get_css_retrieval_strategies()
    )

    results = probe_strategies(
        css_url,
        strategies,
    )

    for result in results.values():
        print(
            f"  "
            f"{result.strategy:<16} "
            f"success={str(result.success):<5} "
            f"size={result.content_size:<8} "
            f"time={result.elapsed_time:.3f}s"
        )

    best_css_strategy = select_best_strategy(
        results
    )

    print(
        f"  CSS Best Strategy: "
        f"{best_css_strategy}"
    )

    return (
        len(results) == 6
        and best_css_strategy is not None
    )


def test_image_probe() -> bool:
    (
        best_strategy,
        html,
        _,
    ) = get_best_html_content()

    if best_strategy is None:
        return False

    if html is None:
        return False

    image_urls = discover_image_urls(
        html,
        TEST_URL,
    )

    if not image_urls:
        return False

    if len(image_urls) <= 2:
        selected_urls = list(
            image_urls
        )
    else:
        import random

        selected_urls = random.sample(
            image_urls,
            2,
        )

    print(
        f"  HTML Best Strategy: "
        f"{best_strategy}"
    )

    print(
        f"  Discovered Images: "
        f"{len(image_urls)}"
    )

    print(
        f"  Sampled Images: "
        f"{len(selected_urls)}"
    )

    for index, url in enumerate(
        selected_urls,
        start=1,
    ):
        print(
            f"  Sample[{index}] {url}"
        )

    strategies = (
        get_image_retrieval_strategies()
    )

    strategy_results = {}

    for image_url in selected_urls:
        print(
            f"  Probe Image: "
            f"{image_url}"
        )

        results = probe_strategies(
            image_url,
            strategies,
        )

        strategy_results[
            image_url
        ] = results

        for result in results.values():
            print(
                f"    "
                f"{result.strategy:<16} "
                f"success={str(result.success):<5} "
                f"size={result.content_size:<8} "
                f"time={result.elapsed_time:.3f}s"
            )

    passed = (
        len(selected_urls) <= 2
        and len(strategy_results)
        == len(selected_urls)
        and all(
            len(results) == 6
            for results
            in strategy_results.values()
        )
    )

    return passed


def test_strategy_evaluation() -> bool:
    large_fast = StrategyEvaluation(
        strategy="large_fast",
        success=True,
        completeness=10000.0,
        content_size=10000,
        elapsed_time=2.0,
    )

    small_fast = StrategyEvaluation(
        strategy="small_fast",
        success=True,
        completeness=5000.0,
        content_size=5000,
        elapsed_time=0.1,
    )

    large_slow = StrategyEvaluation(
        strategy="large_slow",
        success=True,
        completeness=10000.0,
        content_size=10000,
        elapsed_time=5.0,
    )

    large_fast_score = evaluate_strategy(
        large_fast
    )

    small_fast_score = evaluate_strategy(
        small_fast
    )

    large_slow_score = evaluate_strategy(
        large_slow
    )

    passed = (
        large_fast_score
        > small_fast_score
        and large_fast_score
        > large_slow_score
    )

    print(
        f"  Large Fast Score: "
        f"{large_fast_score}"
    )

    print(
        f"  Small Fast Score: "
        f"{small_fast_score}"
    )

    print(
        f"  Large Slow Score: "
        f"{large_slow_score}"
    )

    return passed


def test_best_strategy_selection() -> bool:
    results = {
        "small_fast": StrategyEvaluation(
            strategy="small_fast",
            success=True,
            completeness=5000.0,
            content_size=5000,
            elapsed_time=0.1,
        ),
        "large_slow": StrategyEvaluation(
            strategy="large_slow",
            success=True,
            completeness=10000.0,
            content_size=10000,
            elapsed_time=5.0,
        ),
        "large_fast": StrategyEvaluation(
            strategy="large_fast",
            success=True,
            completeness=10000.0,
            content_size=10000,
            elapsed_time=1.0,
        ),
        "failed": StrategyEvaluation(
            strategy="failed",
            success=False,
            completeness=0.0,
            content_size=0,
            elapsed_time=0.1,
        ),
    }

    best_strategy = select_best_strategy(
        results
    )

    passed = (
        best_strategy
        == "large_fast"
    )

    print(
        f"  Selected Best Strategy: "
        f"{best_strategy}"
    )

    return passed


def test_complete_site_profile() -> bool:
    profile = create_site_profile(
        TEST_URL
    )

    print(
        f"  Site: "
        f"{profile.site.hostname}"
    )

    print(
        f"  Base URL: "
        f"{profile.site.base_url}"
    )

    print(
        f"  HTML Best: "
        f"{profile.html_best_strategy}"
    )

    print(
        f"  CSS Best: "
        f"{profile.css_best_strategy}"
    )

    print(
        f"  Image Best: "
        f"{profile.image_best_strategy}"
    )

    passed = (
        profile.site.hostname
        == "www.digitimes.com.tw"
        and profile.site.base_url
        == "https://www.digitimes.com.tw/"
        and profile.html_best_strategy
        is not None
        and profile.css_best_strategy
        is not None
        and profile.image_best_strategy
        is not None
        and profile.created_at
        is not None
        and profile.updated_at
        is not None
    )

    return passed


def main() -> None:
    print()
    print(
        "AutoSearch V7"
    )
    print(
        "R2 Site Profile Test"
    )
    print(
        f"URL: {TEST_URL}"
    )
    print()

    tests = [
        (
            "Site Identity",
            test_site_identity,
        ),
        (
            "Strategy Registry",
            test_strategy_registry,
        ),
        (
            "HTML Strategy Probe",
            test_html_probe,
        ),
        (
            "HTML Best Strategy",
            test_html_best_strategy,
        ),
        (
            "HTML Best Content",
            test_html_best_content,
        ),
        (
            "CSS Discovery",
            test_css_discovery,
        ),
        (
            "Image Discovery",
            test_image_discovery,
        ),
        (
            "CSS Strategy Probe",
            test_css_probe,
        ),
        (
            "Image Strategy Probe",
            test_image_probe,
        ),
        (
            "Strategy Evaluation",
            test_strategy_evaluation,
        ),
        (
            "Best Strategy Selection",
            test_best_strategy_selection,
        ),
        (
            "Complete Site Profile",
            test_complete_site_profile,
        ),
    ]

    passed_count = 0
    failed_count = 0

    for index, (
        name,
        test_function,
    ) in enumerate(
        tests,
        start=1,
    ):
        try:
            passed = test_function()
        except Exception as exc:
            passed = False

            print(
                f"  ERROR: {type(exc).__name__}: "
                f"{exc}"
            )

        print_result(
            index,
            name,
            passed,
        )

        if passed:
            passed_count += 1
        else:
            failed_count += 1

        print()

    print(
        f"PASS: {passed_count}"
    )

    print(
        f"FAIL: {failed_count}"
    )

    print(
        f"TOTAL: {len(tests)}"
    )

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()