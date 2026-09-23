"""
test_crawler_integration.py

AutoSearch V7

R3 Crawler Integration Test

驗證：

1. MongoDB Site Profile
2. HTML Best Strategy
3. CSS Best Strategy
4. Image Best Strategy
5. Crawler HTML Download
6. Crawler CSS / Image Resource Download
7. CSS Metadata
8. Image Metadata

使用真實 MongoDB
不使用 Mock
"""

from config.settings import TIMEOUT
from crawler.crawler import download, download_resources
from crawler.retrieval.site_profile_service import SiteProfileService


URL = "https://www.digitimes.com.tw/"


def check(condition, message):
    if condition:
        print(f"{message:<35} PASS")
        return True

    print(f"{message:<35} FAIL")
    return False


def main():
    print()
    print("R3 Crawler Integration Test")
    print(f"URL: {URL}")
    print()

    passed = 0
    failed = 0

    profile = None
    html = None
    resources = None

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
        service = SiteProfileService()
        profile = service.get_or_create(URL)

        if profile is not None:
            print(f"{'Site Profile':<35} PASS")
            passed += 1
        else:
            print(f"{'Site Profile':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'Site Profile':<35} FAIL")
        print(exc)
        failed += 1

    print()

    if profile is not None:
        print("Site Profile Strategies")
        print(f"HTML  : {profile.html_best_strategy}")
        print(f"CSS   : {profile.css_best_strategy}")
        print(f"IMAGE : {profile.image_best_strategy}")
        print()

    print("TEST 3 HTML Download")

    try:
        html = download(URL)

        if isinstance(html, str) and len(html) > 0:
            print(f"{'HTML Download':<35} PASS")
            print(f"HTML Size: {len(html)}")
            passed += 1
        else:
            print(f"{'HTML Download':<35} FAIL")
            failed += 1

    except Exception as exc:
        print(f"{'HTML Download':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 4 Resource Download")

    try:
        if not html:
            print(f"{'Resource Download':<35} FAIL")
            print("HTML is empty.")
            failed += 1
        else:
            resources = download_resources(
                html,
                URL,
            )

            if isinstance(resources, dict):
                print(f"{'Resource Download':<35} PASS")
                print(
                    f"CSS Resources   : "
                    f"{len(resources.get('css', []))}"
                )
                print(
                    f"Image Resources : "
                    f"{len(resources.get('images', []))}"
                )
                passed += 1
            else:
                print(f"{'Resource Download':<35} FAIL")
                failed += 1

    except Exception as exc:
        print(f"{'Resource Download':<35} FAIL")
        print(exc)
        failed += 1

    print()

    print("TEST 5 CSS Metadata")

    try:
        css_resources = (
            resources.get("css", [])
            if isinstance(resources, dict)
            else []
        )

        if not css_resources:
            print(f"{'CSS Metadata':<35} FAIL")
            print("No CSS resources.")
            failed += 1
        else:
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

    print("TEST 6 Image Metadata")

    try:
        image_resources = (
            resources.get("images", [])
            if isinstance(resources, dict)
            else []
        )

        if not image_resources:
            print(f"{'Image Metadata':<35} FAIL")
            print("No image resources.")
            failed += 1
        else:
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
        failed += 1
        print(exc)

    print()
    print("R3 Crawler Integration Test Result")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"TOTAL: {passed + failed}")
    print()

    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()