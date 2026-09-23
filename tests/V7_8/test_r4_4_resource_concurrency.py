import time
from threading import Lock

from crawler import crawler


def test_r4_4_resource_concurrency():
    css_urls = [
        "https://example.com/style-1.css",
        "https://example.com/style-2.css",
        "https://example.com/style-3.css",
    ]

    image_urls = [
        "https://example.com/image-1.png",
        "https://example.com/image-2.png",
        "https://example.com/image-3.png",
    ]

    css_state = {
        "active": 0,
        "max_active": 0,
        "started": 0,
        "completed": 0,
    }

    image_state = {
        "active": 0,
        "max_active": 0,
        "started": 0,
        "completed": 0,
    }

    css_lock = Lock()
    image_lock = Lock()

    original_css_download = crawler.download_css_resource
    original_image_download = crawler.download_image_resource

    def fake_css_download(url, headers=None, strategy="http"):
        with css_lock:
            css_state["active"] += 1
            css_state["started"] += 1
            css_state["max_active"] = max(
                css_state["max_active"],
                css_state["active"],
            )

        time.sleep(0.2)

        with css_lock:
            css_state["active"] -= 1
            css_state["completed"] += 1

        return {
            "url": url,
            "content": b"css",
            "content_size": 3,
            "content_hash": "css-test-hash",
            "mime_type": "text/css",
            "file_size": 3,
        }

    def fake_image_download(url, headers=None, strategy="http"):
        with image_lock:
            image_state["active"] += 1
            image_state["started"] += 1
            image_state["max_active"] = max(
                image_state["max_active"],
                image_state["active"],
            )

        time.sleep(0.2)

        with image_lock:
            image_state["active"] -= 1
            image_state["completed"] += 1

        return {
            "url": url,
            "content": b"img",
            "content_size": 3,
            "content_hash": "image-test-hash",
            "mime_type": "image/png",
            "file_size": 3,
        }

    crawler.download_css_resource = fake_css_download
    crawler.download_image_resource = fake_image_download

    try:
        print()
        print("R4.4 CSS/Image Resource Concurrency Test")
        print()

        print(f"CSS_CONCURRENCY   = {crawler.CSS_CONCURRENCY}")
        print(f"IMAGE_CONCURRENCY = {crawler.IMAGE_CONCURRENCY}")

        css_start = time.perf_counter()

        css_results = crawler._download_css_resources(
            css_urls,
            {},
            "referer",
        )

        css_elapsed = time.perf_counter() - css_start

        image_start = time.perf_counter()

        image_results = crawler._download_image_resources(
            image_urls,
            {},
            "cookie_session",
        )

        image_elapsed = time.perf_counter() - image_start

        passed = 0
        failed = 0

        def check(name, condition):
            nonlocal passed, failed

            if condition:
                print(f"PASS: {name}")
                passed += 1
            else:
                print(f"FAIL: {name}")
                failed += 1

        check(
            "CSS Concurrency Setting = 2",
            crawler.CSS_CONCURRENCY == 2,
        )

        check(
            "Image Concurrency Setting = 2",
            crawler.IMAGE_CONCURRENCY == 2,
        )

        check(
            "All CSS Resources Returned",
            len(css_results) == len(css_urls),
        )

        check(
            "All Image Resources Returned",
            len(image_results) == len(image_urls),
        )

        check(
            "All CSS Downloads Started",
            css_state["started"] == len(css_urls),
        )

        check(
            "All CSS Downloads Completed",
            css_state["completed"] == len(css_urls),
        )

        check(
            "CSS Max Concurrent = 2",
            css_state["max_active"] == 2,
        )

        check(
            "All Image Downloads Started",
            image_state["started"] == len(image_urls),
        )

        check(
            "All Image Downloads Completed",
            image_state["completed"] == len(image_urls),
        )

        check(
            "Image Max Concurrent = 2",
            image_state["max_active"] == 2,
        )

        check(
            "CSS Concurrent Execution Time",
            css_elapsed < 0.55,
        )

        check(
            "Image Concurrent Execution Time",
            image_elapsed < 0.55,
        )

        print()
        print(f"CSS Max Concurrent    : {css_state['max_active']}")
        print(f"Image Max Concurrent  : {image_state['max_active']}")
        print(f"CSS Elapsed Time      : {css_elapsed:.3f}s")
        print(f"Image Elapsed Time    : {image_elapsed:.3f}s")
        print()

        print(f"PASS: {passed}")
        print(f"FAIL: {failed}")
        print(f"TOTAL: {passed + failed}")

        assert failed == 0

    finally:
        crawler.download_css_resource = original_css_download
        crawler.download_image_resource = original_image_download


if __name__ == "__main__":
    test_r4_4_resource_concurrency()