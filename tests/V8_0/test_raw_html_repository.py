"""
tests/V8_0/test_raw_html_repository.py

AutoSearch V5

Raw HTML Repository Tests
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from database.raw_html_repository import (
    RawHTMLRepository,
)


def test_find_versions_by_url_returns_all_snapshots():
    repository = RawHTMLRepository()

    url = "https://example.com/v8-0/all"
    now = datetime.now(timezone.utc)

    inserted_ids = []

    try:
        for offset in [0, 1, 2]:
            result = repository.collection.insert_one(
                {
                    "url": url,
                    "html": f"<html>{offset}</html>",
                    "content_hash": f"hash-{offset}",
                    "created_at": now - timedelta(
                        days=offset
                    ),
                }
            )

            inserted_ids.append(
                result.inserted_id
            )

        versions = repository.find_versions_by_url(
            url
        )

        assert len(versions) == 3

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )


def test_find_versions_by_url_sorts_latest_first():
    repository = RawHTMLRepository()

    url = "https://example.com/v8-0/sort"
    now = datetime.now(timezone.utc)

    inserted_ids = []

    try:
        dates = [
            now - timedelta(days=3),
            now - timedelta(days=1),
            now - timedelta(days=2),
        ]

        for index, created_at in enumerate(dates):
            result = repository.collection.insert_one(
                {
                    "url": url,
                    "html": f"<html>{index}</html>",
                    "content_hash": f"hash-sort-{index}",
                    "created_at": created_at,
                }
            )

            inserted_ids.append(
                result.inserted_id
            )

        versions = repository.find_versions_by_url(
            url
        )

        assert len(versions) == 3

        returned_dates = [
            version["created_at"]
            for version in versions
        ]

        assert returned_dates == sorted(
            returned_dates,
            reverse=True,
        )

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )


def test_find_versions_by_url_removes_duplicate_created_at():
    repository = RawHTMLRepository()

    url = "https://example.com/v8-0/duplicate"

    created_at = datetime.now(
        timezone.utc
    )

    older_created_at = (
        created_at - timedelta(days=1)
    )

    inserted_ids = []

    try:
        documents = [
            {
                "url": url,
                "html": "<html>duplicate-1</html>",
                "content_hash": "duplicate-hash-1",
                "created_at": created_at,
            },
            {
                "url": url,
                "html": "<html>duplicate-2</html>",
                "content_hash": "duplicate-hash-2",
                "created_at": created_at,
            },
            {
                "url": url,
                "html": "<html>older</html>",
                "content_hash": "older-hash",
                "created_at": older_created_at,
            },
        ]

        for document in documents:
            result = repository.collection.insert_one(
                document
            )

            inserted_ids.append(
                result.inserted_id
            )

        versions = repository.find_versions_by_url(
            url
        )

        assert len(versions) == 2

        returned_dates = [
            version["created_at"]
            for version in versions
        ]

        assert returned_dates[0] == created_at.replace(
            microsecond=(created_at.microsecond // 1000) * 1000
        )

        assert returned_dates[1] == older_created_at.replace(
            microsecond=(older_created_at.microsecond // 1000) * 1000
        )

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )


def test_find_versions_by_url_ignores_other_urls():
    repository = RawHTMLRepository()

    target_url = "https://example.com/v8-0/target"
    other_url = "https://example.com/v8-0/other"

    now = datetime.now(timezone.utc)

    inserted_ids = []

    try:
        documents = [
            {
                "url": target_url,
                "html": "<html>target-1</html>",
                "content_hash": "target-hash-1",
                "created_at": now,
            },
            {
                "url": target_url,
                "html": "<html>target-2</html>",
                "content_hash": "target-hash-2",
                "created_at": now - timedelta(
                    days=1
                ),
            },
            {
                "url": other_url,
                "html": "<html>other</html>",
                "content_hash": "other-hash",
                "created_at": now,
            },
        ]

        for document in documents:
            result = repository.collection.insert_one(
                document
            )

            inserted_ids.append(
                result.inserted_id
            )

        versions = repository.find_versions_by_url(
            target_url
        )

        assert len(versions) == 2

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )


def test_find_versions_by_url_returns_empty_for_missing_url():
    repository = RawHTMLRepository()

    versions = repository.find_versions_by_url(
        "https://example.com/v8-0/not-found"
    )

    assert versions == []


def test_find_versions_by_url_returns_empty_for_empty_url():
    repository = RawHTMLRepository()

    assert repository.find_versions_by_url(
        None
    ) == []

    assert repository.find_versions_by_url(
        ""
    ) == []

    assert repository.find_versions_by_url(
        "   "
    ) == []


def test_find_versions_by_url_normalizes_datetime_to_utc():
    repository = RawHTMLRepository()

    url = "https://example.com/v8-0/timezone"

    created_at = datetime(
        2026,
        8,
        29,
        14,
        20,
        tzinfo=timezone(
            timedelta(hours=8)
        ),
    )

    expected_utc = datetime(
        2026,
        8,
        29,
        6,
        20,
        tzinfo=timezone.utc,
    )

    inserted_ids = []

    try:
        result = repository.collection.insert_one(
            {
                "url": url,
                "html": "<html>timezone</html>",
                "content_hash": "timezone-hash",
                "created_at": created_at,
            }
        )

        inserted_ids.append(
            result.inserted_id
        )

        versions = repository.find_versions_by_url(
            url
        )

        assert len(versions) == 1
        assert versions[0]["created_at"] == expected_utc
        assert versions[0]["created_at"].tzinfo == timezone.utc

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )


def test_find_versions_by_url_does_not_delete_snapshots():
    repository = RawHTMLRepository()

    url = "https://example.com/v8-0/preserve"
    created_at = datetime.now(timezone.utc)

    inserted_ids = []

    try:
        for index in range(2):
            result = repository.collection.insert_one(
                {
                    "url": url,
                    "html": f"<html>{index}</html>",
                    "content_hash": f"preserve-{index}",
                    "created_at": created_at,
                }
            )

            inserted_ids.append(
                result.inserted_id
            )

        versions = repository.find_versions_by_url(
            url
        )

        assert len(versions) == 1

        snapshot_count = repository.collection.count_documents(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )

        assert snapshot_count == 2

    finally:
        repository.collection.delete_many(
            {
                "_id": {
                    "$in": inserted_ids
                }
            }
        )