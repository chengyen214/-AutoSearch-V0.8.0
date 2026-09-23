"""
test_r4_5_session_reuse.py

AutoSearch V7

R4.5 Session / Connection Reuse Test

測試：

1. 同一 Thread + 同一 Strategy 重複使用 Session
2. 不同 Strategy 使用不同 Session
3. 多張 Image Retrieval 重複使用 Session
4. RetrievalContext cleanup
"""

from __future__ import annotations

from unittest.mock import patch

from crawler.retrieval.image_retrieval import (
    retrieve_image,
)
from crawler.retrieval.retrieval_context import (
    RetrievalContext,
)


class FakeResponse:
    def __init__(self, url: str):
        self.status_code = 200
        self.headers = {
            "Content-Type": "image/png",
        }
        self.content = b"fake-image-data"
        self.url = url


class FakeSession:
    created_count = 0
    closed_count = 0
    request_count = 0

    def __init__(self):
        type(self).created_count += 1
        self.closed = False

    def get(
        self,
        url,
        timeout=None,
        **kwargs,
    ):
        type(self).request_count += 1

        return FakeResponse(url)

    def close(self):
        if not self.closed:
            self.closed = True
            type(self).closed_count += 1


def reset_fake_session():
    FakeSession.created_count = 0
    FakeSession.closed_count = 0
    FakeSession.request_count = 0


def test_same_strategy_reuses_session():
    reset_fake_session()

    with patch(
        "crawler.retrieval.retrieval_context.requests.Session",
        FakeSession,
    ):
        context = RetrievalContext()

        session_1 = context.get_session("http")
        session_2 = context.get_session("http")

        passed = session_1 is session_2

        context.close()

    return passed


def test_different_strategies_use_different_sessions():
    reset_fake_session()

    with patch(
        "crawler.retrieval.retrieval_context.requests.Session",
        FakeSession,
    ):
        context = RetrievalContext()

        http_session = context.get_session("http")
        session_session = context.get_session("session")

        passed = (
            http_session is not session_session
            and FakeSession.created_count == 2
        )

        context.close()

    return passed


def test_multiple_images_reuse_session():
    reset_fake_session()

    image_urls = [
        "https://example.com/image-1.png",
        "https://example.com/image-2.png",
        "https://example.com/image-3.png",
    ]

    with patch(
        "crawler.retrieval.retrieval_context.requests.Session",
        FakeSession,
    ):
        context = RetrievalContext()

        results = []

        for url in image_urls:
            result = retrieve_image(
                url,
                strategy="http",
                retrieval_context=context,
            )

            results.append(result)

        passed = (
            len(results) == 3
            and all(result.success for result in results)
            and FakeSession.created_count == 1
            and FakeSession.request_count == 3
        )

        context.close()

    return passed


def test_context_cleanup():
    reset_fake_session()

    with patch(
        "crawler.retrieval.retrieval_context.requests.Session",
        FakeSession,
    ):
        context = RetrievalContext()

        context.get_session("http")
        context.get_session("session")
        context.get_session("referer")

        context.close()

        passed = (
            FakeSession.created_count == 3
            and FakeSession.closed_count == 3
        )

    return passed


def main():
    print("=" * 60)
    print("AutoSearch V7")
    print("R4.5 Session / Connection Reuse Test")
    print("=" * 60)

    tests = [
        (
            "TEST 1 Same Strategy Session Reuse",
            test_same_strategy_reuses_session,
        ),
        (
            "TEST 2 Different Strategy Session Isolation",
            test_different_strategies_use_different_sessions,
        ),
        (
            "TEST 3 Multiple Image Session Reuse",
            test_multiple_images_reuse_session,
        ),
        (
            "TEST 4 RetrievalContext Cleanup",
            test_context_cleanup,
        ),
    ]

    passed_count = 0
    failed_count = 0

    for name, test_function in tests:
        print()
        print(name)
        print("-" * 60)

        try:
            passed = test_function()

            if passed:
                print(f"{name}: PASS")
                passed_count += 1
            else:
                print(f"{name}: FAIL")
                failed_count += 1

        except Exception as exc:
            print(f"{name}: FAIL")
            print(f"error        : {exc}")
            failed_count += 1

    print()
    print("=" * 60)
    print(f"PASS: {passed_count}")
    print(f"FAIL: {failed_count}")
    print(f"TOTAL: {passed_count + failed_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()