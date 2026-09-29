"""
tests/V8_0/test_snapshot_schema.py

檢查 MongoDB Raw HTML Snapshot 實際資料結構。
"""

from pymongo import MongoClient

from config.mongo_config import (
    MONGO_RAW_HTML_COLLECTION,
)


MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "autosearch"


def test_snapshot_schema():
    client = MongoClient(
        MONGO_URI
    )

    collection = client[
        DATABASE_NAME
    ][
        MONGO_RAW_HTML_COLLECTION
    ]

    snapshot = collection.find_one(
        {}
    )

    assert snapshot is not None

    print("\n")
    print("=" * 60)
    print("MongoDB Raw HTML Snapshot Schema")
    print("=" * 60)

    print(
        "Collection:",
        MONGO_RAW_HTML_COLLECTION
    )

    print(
        "Fields:"
    )

    for key in snapshot:
        value = snapshot[key]

        if isinstance(
            value,
            str
        ):
            print(
                f"  {key}: "
                f"type=str, "
                f"length={len(value)}"
            )

        elif isinstance(
            value,
            (list, dict)
        ):
            print(
                f"  {key}: "
                f"type={type(value).__name__}, "
                f"length={len(value)}"
            )

        else:
            print(
                f"  {key}: "
                f"type={type(value).__name__}"
            )

    print("=" * 60)

    client.close()