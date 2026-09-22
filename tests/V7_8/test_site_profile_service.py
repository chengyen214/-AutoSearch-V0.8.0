"""
test_site_profile_service.py

AutoSearch V7

R2.5 Site Profile Service Integration Test

測試：

1. MongoDB Connection
2. 第一次 URL 查詢
3. Site Profile 建立
4. MongoDB 實際保存
5. 同來源網站不同 URL 查詢
6. 第二次直接取得既有 Profile
7. 驗證兩個 URL 使用相同 Site Profile
8. 驗證 MongoDB 只保存最終 Best Strategy
"""

from crawler.retrieval.site_profile_service import (
    SiteProfileService,
)

from crawler.retrieval.site_profile_repository import (
    SiteProfileRepository,
)


TEST_URL = (
    "https://www.digitimes.com.tw/"
    "research/report-category/"
    "?CnlID=3&cat=CSE"
)

SAME_SITE_URL = (
    "https://www.digitimes.com.tw/"
)


def print_section(title: str) -> None:
    print()
    print(title)


def main() -> None:
    print(
        "AutoSearch V7"
    )

    print(
        "R2.5 Site Profile Service Integration Test"
    )

    print(
        f"URL: {TEST_URL}"
    )

    service = SiteProfileService()

    repository = SiteProfileRepository()

    print_section(
        "TEST 1  MongoDB Connection"
    )

    try:
        repository.collection.database.command(
            "ping"
        )

        print(
            "PASS"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 2  First URL Site Profile"
    )

    try:
        profile = service.get_or_create(
            TEST_URL
        )

        print(
            "PASS"
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

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 3  MongoDB Site Profile"
    )

    try:
        document = (
            repository.find_by_base_url(
                profile.site.base_url
            )
        )

        if document is None:
            print(
                "FAIL: "
                "Site Profile not found in MongoDB"
            )
            return

        print(
            "PASS"
        )

        print(
            f"  MongoDB ID: "
            f"{document.get('_id')}"
        )

        print(
            f"  Base URL: "
            f"{document['site']['base_url']}"
        )

        print(
            f"  HTML Best: "
            f"{document['html']['best_strategy']}"
        )

        print(
            f"  CSS Best: "
            f"{document['css']['best_strategy']}"
        )

        print(
            f"  Image Best: "
            f"{document['image']['best_strategy']}"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 4  Same Site Different URL"
    )

    try:
        same_site_profile = (
            service.get_or_create(
                SAME_SITE_URL
            )
        )

        if (
            same_site_profile.site.base_url
            != profile.site.base_url
        ):
            print(
                "FAIL: "
                "Base URL is different"
            )
            return

        print(
            "PASS"
        )

        print(
            f"  URL 1 Base URL: "
            f"{profile.site.base_url}"
        )

        print(
            f"  URL 2 Base URL: "
            f"{same_site_profile.site.base_url}"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 5  Existing Profile Lookup"
    )

    try:
        existing_document = (
            repository.find_by_base_url(
                profile.site.base_url
            )
        )

        if existing_document is None:
            print(
                "FAIL: "
                "Existing Site Profile not found"
            )
            return

        existing_profile = (
            service._document_to_profile(
                existing_document
            )
        )

        if (
            existing_profile.site.base_url
            != profile.site.base_url
        ):
            print(
                "FAIL: "
                "Returned profile mismatch"
            )
            return

        if (
            existing_profile.html_best_strategy
            != profile.html_best_strategy
        ):
            print(
                "FAIL: "
                "HTML Best Strategy mismatch"
            )
            return

        if (
            existing_profile.css_best_strategy
            != profile.css_best_strategy
        ):
            print(
                "FAIL: "
                "CSS Best Strategy mismatch"
            )
            return

        if (
            existing_profile.image_best_strategy
            != profile.image_best_strategy
        ):
            print(
                "FAIL: "
                "Image Best Strategy mismatch"
            )
            return

        print(
            "PASS"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 6  Storage Fields"
    )

    try:
        allowed_fields = {
            "_id",
            "site",
            "html",
            "css",
            "image",
            "created_at",
            "updated_at",
        }

        unexpected_fields = (
            set(document.keys())
            - allowed_fields
        )

        if unexpected_fields:
            print(
                "FAIL: "
                f"Unexpected fields: "
                f"{unexpected_fields}"
            )
            return

        print(
            "PASS"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print_section(
        "TEST 7  Final MongoDB Count"
    )

    try:
        count = repository.collection.count_documents(
            {
                "site.base_url":
                    profile.site.base_url
            }
        )

        if count != 1:
            print(
                "FAIL: "
                f"Expected 1 document, got {count}"
            )
            return

        print(
            "PASS"
        )

        print(
            f"  Site Profile Count: {count}"
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        return

    print()
    print(
        "PASS: 7"
    )
    print(
        "FAIL: 0"
    )
    print(
        "TOTAL: 7"
    )


if __name__ == "__main__":
    main()