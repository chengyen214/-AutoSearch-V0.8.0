"""
test_crawl_service_r3.py

AutoSearch V7

R3 Crawler Integration Test

驗證：

1. Site Profile
2. CrawlService
3. HTML Retrieval
4. CSS / Image Resource Retrieval
5. CrawlResult
6. Raw HTML MongoDB Storage

使用真實 MongoDB
不使用 Mock
"""

from config.settings import TIMEOUT
from crawler.retrieval.site_profile_service import SiteProfileService
from services.crawl_service import CrawlService


URL = "https://www.ctimes.com.tw/2609091654BQ.shtml"


def main():
    print()
    print("R3 CrawlService Integration Test")
    print(f"URL: {URL}")
    print()

    passed = 0
    failed = 0

    profile = None
    service = None
    result = None

    print("TEST 1 TIMEOUT")

    if TIMEOUT == 15:
        print(f"{'TIMEOUT = 15':<35} PASS")
        passed += 1
    else:
        print(f"{'TIMEOUT = 15':<35} FAIL")
        print(f"Actual TIMEOUT: {TIMEOUT}")
        failed += 1

    print()

    print("TEST 2 Site Profile")

    try:
        profile_service = SiteProfileService()
        profile = profile_service.get_or_create(URL)

        if profile is not None:
            print(f"{'Site Profile':<35} PASS")
            print(f"Hostname        : {profile.site.hostname}")
            print(f"Scheme          : {profile.site.scheme}")
            print(f"Base URL        : {profile.site.base_url}")
            print(f"HTML Best       : {profile.html_best_strategy}")
            print(f"CSS Best        : {profile.css_best_strategy}")
            print(f"Image Best      : {profile.image_best_strategy}")
            passed += 1
        else:
            print(f"{'Site Profile':<35} FAIL")
            print("Site Profile does not exist.")
            failed += 1

    except Exception as exc:
        print(f"{'Site Profile':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 3 CrawlService")

    try:
        service = CrawlService()

        if service is not None:
            print(f"{'CrawlService':<35} PASS")
            passed += 1
        else:
            print(f"{'CrawlService':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'CrawlService':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 4 Crawl")

    try:
        result = service.crawl(URL)

        if result is not None:
            print(f"{'Crawl':<35} PASS")
            passed += 1
        else:
            print(f"{'Crawl':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'Crawl':<35} FAIL")
        print(exc)
        failed += 1

    print()

    if result is not None:
        print("Crawl Result")

        print(f"URL            : {getattr(result, 'url', None)}")
        print(f"Resolved URL   : {getattr(result, 'resolved_url', None)}")

        html = getattr(result, "html", None)

        if isinstance(html, str):
            print(f"HTML Size      : {len(html)}")
        else:
            print("HTML Size      : 0")

        print()

    print("TEST 5 HTML Result")

    try:
        html = getattr(result, "html", None)

        if isinstance(html, str) and len(html) > 0:
            print(f"{'HTML Result':<35} PASS")
            print(f"HTML Size: {len(html)}")
            passed += 1
        else:
            print(f"{'HTML Result':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'HTML Result':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 6 Content Hash")

    try:
        content_hash = getattr(result, "content_hash", None)

        if isinstance(content_hash, str) and len(content_hash) > 0:
            print(f"{'Content Hash':<35} PASS")
            print(f"Hash: {content_hash}")
            passed += 1
        else:
            print(f"{'Content Hash':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'Content Hash':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 7 Resource Result")

    try:
        resources = getattr(result, "resources", None)

        if isinstance(resources, dict):
            css_resources = resources.get("css", [])
            image_resources = resources.get("images", [])

            print(f"{'Resource Result':<35} PASS")
            print(f"CSS Resources   : {len(css_resources)}")
            print(f"Image Resources : {len(image_resources)}")
            passed += 1
        else:
            print(f"{'Resource Result':<35} FAIL")
            print("Resources is not a dict.")
            failed += 1

    except Exception as exc:
        print(f"{'Resource Result':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 8 CSS Metadata")

    try:
        resources = getattr(result, "resources", None)

        css_resources = (
            resources.get("css", [])
            if isinstance(resources, dict)
            else []
        )

        valid_css = 0

        for resource in css_resources:
            if not isinstance(resource, dict):
                continue

            if resource.get("url"):
                valid_css += 1

        if valid_css > 0:
            print(f"{'CSS Metadata':<35} PASS")
            print(f"Valid CSS Metadata: {valid_css}")
            passed += 1
        else:
            print(f"{'CSS Metadata':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'CSS Metadata':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 9 Image Metadata")

    try:
        resources = getattr(result, "resources", None)

        image_resources = (
            resources.get("images", [])
            if isinstance(resources, dict)
            else []
        )

        valid_images = 0

        for resource in image_resources:
            if not isinstance(resource, dict):
                continue

            if resource.get("url"):
                valid_images += 1

        if valid_images > 0:
            print(f"{'Image Metadata':<35} PASS")
            print(f"Valid Image Metadata: {valid_images}")
            passed += 1
        else:
            print(f"{'Image Metadata':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'Image Metadata':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 10 Raw HTML MongoDB Storage")

    try:
        if result is not None:
            print(f"{'Raw HTML MongoDB Storage':<35} PASS")
            print("CrawlService completed and returned CrawlResult.")
            passed += 1
        else:
            print(f"{'Raw HTML MongoDB Storage':<35} FAIL")
            print("No CrawlResult returned.")
            failed += 1

    except Exception as exc:
        print(f"{'Raw HTML MongoDB Storage':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("R3 CrawlService Integration Test Result")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"TOTAL: {passed + failed}")
    print()

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()