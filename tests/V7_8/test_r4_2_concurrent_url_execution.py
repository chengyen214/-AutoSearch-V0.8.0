import threading
import time
from dataclasses import dataclass

from services.job_executor_bridge import JobExecutorBridge


@dataclass
class MockSearchResult:
    url: str
    title: str
    source: str


@dataclass
class MockCrawlResult:
    url: str
    html: str


class ConcurrentCrawlService:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_count = 0
        self.max_active_count = 0
        self.started_urls = []
        self.completed_urls = []

    def crawl_result(self, search_result):
        with self.lock:
            self.active_count += 1

            if self.active_count > self.max_active_count:
                self.max_active_count = self.active_count

            self.started_urls.append(search_result.url)

        time.sleep(0.5)

        with self.lock:
            self.active_count -= 1
            self.completed_urls.append(search_result.url)

        return MockCrawlResult(
            url=search_result.url,
            html=f"<html>{search_result.url}</html>",
        )


def create_search_results():
    return [
        MockSearchResult(
            url="https://example.com/article-1",
            title="Article 1",
            source="test",
        ),
        MockSearchResult(
            url="https://example.com/article-2",
            title="Article 2",
            source="test",
        ),
        MockSearchResult(
            url="https://example.com/article-3",
            title="Article 3",
            source="test",
        ),
    ]


def test_bridge_initialization():
    crawl_service = ConcurrentCrawlService()

    bridge = JobExecutorBridge(
        crawl_service=crawl_service,
    )

    return bridge


def test_real_concurrent_execution():
    crawl_service = ConcurrentCrawlService()

    bridge = JobExecutorBridge(
        crawl_service=crawl_service,
    )

    search_results = create_search_results()

    start_time = time.perf_counter()

    results = bridge._crawl_search_results(
        search_results
    )

    elapsed = time.perf_counter() - start_time

    return (
        results,
        crawl_service,
        elapsed,
    )


def main():
    passed = 0
    failed = 0

    print(
        "R4.2 Real Concurrent URL Execution Test Result"
    )

    try:
        bridge = test_bridge_initialization()

        if bridge is not None:
            print("PASS: Bridge Initialization")
            passed += 1
        else:
            print("FAIL: Bridge Initialization")
            failed += 1

    except Exception as e:
        print(
            f"FAIL: Bridge Initialization - {e}"
        )
        failed += 1

    try:
        results, crawl_service, elapsed = (
            test_real_concurrent_execution()
        )

        if len(results) == 3:
            print("PASS: All URLs Crawled")
            passed += 1
        else:
            print(
                "FAIL: All URLs Crawled"
            )
            failed += 1

        if all(
            result is not None
            for result in results
        ):
            print("PASS: All Crawl Results Returned")
            passed += 1
        else:
            print(
                "FAIL: All Crawl Results Returned"
            )
            failed += 1

        if crawl_service.max_active_count >= 2:
            print(
                "PASS: Concurrent Execution Detected"
            )
            passed += 1
        else:
            print(
                "FAIL: Concurrent Execution Not Detected"
            )
            failed += 1

        if crawl_service.max_active_count <= 2:
            print(
                "PASS: Concurrency Limit = 2"
            )
            passed += 1
        else:
            print(
                "FAIL: Concurrency Limit Exceeded"
            )
            failed += 1

        if elapsed < 1.3:
            print(
                "PASS: Concurrent Execution Time"
            )
            passed += 1
        else:
            print(
                "FAIL: Execution Time Indicates Sequential Execution"
            )
            failed += 1

        print(
            f"Max Concurrent Crawls: "
            f"{crawl_service.max_active_count}"
        )

        print(
            f"Started URLs: "
            f"{len(crawl_service.started_urls)}"
        )

        print(
            f"Completed URLs: "
            f"{len(crawl_service.completed_urls)}"
        )

        print(
            f"Elapsed Time: "
            f"{elapsed:.3f}s"
        )

    except Exception as e:
        print(
            f"FAIL: Real Concurrent Execution - {e}"
        )
        failed += 1

    total = passed + failed

    print()
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"TOTAL: {total}")

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()