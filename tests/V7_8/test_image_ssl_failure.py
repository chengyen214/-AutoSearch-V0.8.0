"""
test_image_ssl_failure.py

AutoSearch V7

單獨測試 Image SSL Fallback。
"""

from crawler.retrieval.image_retrieval import retrieve_image


URLS = [
    "https://img.digitimes.com/newsimg/2026/0922/769340-1-2z10k.jpg",
    "https://img.digitimes.com/newsimg/2026/0922/769348-1-kj65h.png",
    "https://img.digitimes.com/tw/rwd/v2023/img/footer/appstore.png",
]


def main():
    print()
    print("Image SSL Fallback Test")
    print()

    for index, url in enumerate(URLS, start=1):
        print(f"TEST {index}")
        print(f"URL: {url}")

        result = retrieve_image(
            url,
            strategy="ssl_fallback",
        )

        print(f"Success      : {result.success}")
        print(f"Strategy     : {result.strategy}")
        print(f"Status Code  : {result.status_code}")
        print(f"Content Size : {result.content_size}")
        print(f"Elapsed Time : {result.elapsed_time:.3f}s")
        print(f"Error        : {result.error}")
        print()


if __name__ == "__main__":
    main()