"""
tests/V8_0/test_r10_4_integration.py

AutoSearch V7

R10.4 Real Integration Test

驗證：

    MongoDB Snapshot History
        ↓
    SnapshotDocument
        ↓
    SnapshotDifference
        ↓
    ArchiveRAGContext
        ↓
    Existing ChromaDB RAG
        ↓
    RAGQuery
        ↓
    Groq

注意：

    Historical Snapshot 不建立 ChromaDB Index。
    Historical Snapshot 不進行 Embedding。
    不修改 MongoDB Snapshot。
"""

import logging

from database.raw_html_repository import RawHTMLRepository
from rag.archive_rag_context import ArchiveRAGContext
from rag.rag_query import RAGQuery
from rag.snapshot_document import SnapshotDocument
from rag.snapshot_difference import SnapshotDifference


MIN_SNAPSHOT_COUNT = 2


def _get_snapshot_urls(repository):
    """
    從真實 MongoDB 取得 Snapshot URL。
    """

    return repository.collection.distinct(
        "url"
    )


def _get_snapshot_history(repository, url):
    """
    取得指定 URL 的完整 Snapshot History。
    """

    versions = repository.find_versions_by_url(
        url
    )

    snapshots = []

    for version in versions:
        mongo_id = version.get(
            "mongo_id"
        )

        if not mongo_id:
            continue

        snapshot = repository.find_by_id(
            mongo_id
        )

        if snapshot is None:
            continue

        snapshots.append(
            snapshot
        )

    snapshots.sort(
        key=lambda snapshot: snapshot.get(
            "created_at"
        ),
        reverse=True,
    )

    return snapshots


def _build_snapshot_documents(snapshots):
    """
    將 Snapshot 轉換成 SnapshotDocument。
    """

    documents = []
    errors = {}

    for snapshot in snapshots:

        try:
            document = SnapshotDocument.from_snapshot(
                snapshot
            )
        except Exception as exc:
            error_type = type(exc).__name__
            error_message = str(exc)

            key = (
                error_type,
                error_message,
            )

            errors[key] = (
                errors.get(key, 0)
                + 1
            )

            continue

        documents.append(
            (
                snapshot,
                document,
            )
        )

    return documents, errors


def _merge_errors(target, source):
    """
    合併 SnapshotDocument 錯誤統計。
    """

    for key, count in source.items():
        target[key] = (
            target.get(key, 0)
            + count
        )


def _find_snapshot_case(repository):
    """
    找到具有至少兩個 Snapshot 且內容不同的真實 MongoDB Case。
    """

    urls = _get_snapshot_urls(
        repository
    )

    checked_urls = 0
    multi_snapshot_urls = 0
    document_success = 0
    document_failures = 0
    difference_checked = 0
    changed_cases = 0
    document_errors = {}

    for url in urls:

        if not url:
            continue

        checked_urls += 1

        snapshots = _get_snapshot_history(
            repository=repository,
            url=url,
        )

        if len(snapshots) < MIN_SNAPSHOT_COUNT:
            continue

        multi_snapshot_urls += 1

        documents, errors = (
            _build_snapshot_documents(
                snapshots
            )
        )

        _merge_errors(
            document_errors,
            errors,
        )

        document_success += len(
            documents
        )

        document_failures += (
            len(snapshots)
            - len(documents)
        )

        if len(documents) < MIN_SNAPSHOT_COUNT:
            continue

        latest_snapshot, latest_document = (
            documents[0]
        )

        for (
            historical_snapshot,
            historical_document,
        ) in documents[1:]:

            difference_checked += 1

            try:
                difference = SnapshotDifference.compare(
                    historical=historical_document,
                    latest=latest_document,
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if not difference.has_changes:
                continue

            changed_cases += 1

            return {
                "case": {
                    "url": url,
                    "historical_snapshot": (
                        historical_snapshot
                    ),
                    "latest_snapshot": (
                        latest_snapshot
                    ),
                    "historical_document": (
                        historical_document
                    ),
                    "latest_document": (
                        latest_document
                    ),
                    "difference": difference,
                },
                "checked_urls": checked_urls,
                "multi_snapshot_urls": (
                    multi_snapshot_urls
                ),
                "document_success": (
                    document_success
                ),
                "document_failures": (
                    document_failures
                ),
                "difference_checked": (
                    difference_checked
                ),
                "changed_cases": changed_cases,
                "document_errors": (
                    document_errors
                ),
            }

    return {
        "case": None,
        "checked_urls": checked_urls,
        "multi_snapshot_urls": (
            multi_snapshot_urls
        ),
        "document_success": (
            document_success
        ),
        "document_failures": (
            document_failures
        ),
        "difference_checked": (
            difference_checked
        ),
        "changed_cases": (
            changed_cases
        ),
        "document_errors": (
            document_errors
        ),
    }


def _build_query(snapshot):
    """
    使用 SnapshotDocument 建立 RAG Query。
    """

    try:
        document = SnapshotDocument.from_snapshot(
            snapshot
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    title = (
        document.title or ""
    ).strip()

    if title:
        return title

    content = (
        document.content or ""
    ).strip()

    if content:
        return content[:120]

    return (
        document.url or ""
    ).strip() or None


def _find_rag_case(
    repository,
    archive_context,
):
    """
    找到 MongoDB 多版本 Snapshot 且
    Latest Article 可被既有 ChromaDB Retrieval 找到的 Case。
    """

    urls = _get_snapshot_urls(
        repository
    )

    checked_urls = 0
    multi_snapshot_urls = 0
    retrieval_attempts = 0
    retrieval_success = 0
    empty_context = 0
    retrieval_failures = 0
    query_failures = 0

    for url in urls:

        if not url:
            continue

        checked_urls += 1

        snapshots = _get_snapshot_history(
            repository=repository,
            url=url,
        )

        if len(snapshots) < MIN_SNAPSHOT_COUNT:
            continue

        multi_snapshot_urls += 1

        latest_snapshot = snapshots[0]

        query = _build_query(
            latest_snapshot
        )

        if not query:
            query_failures += 1
            continue

        retrieval_attempts += 1

        try:
            latest_context = (
                archive_context.build_latest_context(
                    query=query,
                    urls=[url],
                )
            )
        except Exception:
            retrieval_failures += 1
            continue

        if not isinstance(
            latest_context,
            dict,
        ):
            retrieval_failures += 1
            continue

        context_text = (
            latest_context.get(
                "context_text",
                "",
            )
        )

        if not isinstance(
            context_text,
            str,
        ):
            empty_context += 1
            continue

        if not context_text.strip():
            empty_context += 1
            continue

        retrieval_success += 1

        return {
            "case": {
                "url": url,
                "query": query,
                "latest_snapshot": (
                    latest_snapshot
                ),
                "latest_context": (
                    latest_context
                ),
                "snapshots": snapshots,
            },
            "checked_urls": checked_urls,
            "multi_snapshot_urls": (
                multi_snapshot_urls
            ),
            "retrieval_attempts": (
                retrieval_attempts
            ),
            "retrieval_success": (
                retrieval_success
            ),
            "empty_context": empty_context,
            "retrieval_failures": (
                retrieval_failures
            ),
            "query_failures": query_failures,
        }

    return {
        "case": None,
        "checked_urls": checked_urls,
        "multi_snapshot_urls": (
            multi_snapshot_urls
        ),
        "retrieval_attempts": (
            retrieval_attempts
        ),
        "retrieval_success": (
            retrieval_success
        ),
        "empty_context": empty_context,
        "retrieval_failures": (
            retrieval_failures
        ),
        "query_failures": query_failures,
    }


def _print_snapshot_error_summary(errors):
    """
    印出 SnapshotDocument 錯誤統計。
    """

    if not errors:
        return

    print()
    print(
        "SnapshotDocument Error Summary"
    )
    print(
        "=" * 60
    )

    sorted_errors = sorted(
        errors.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    for (
        error_type,
        error_message,
    ), count in sorted_errors:

        print(
            f"{count}x "
            f"{error_type}: "
            f"{error_message}"
        )


def test_r10_4_real_snapshot_integration():
    """
    驗證 MongoDB Snapshot → Difference → ArchiveRAGContext。
    """

    repository = RawHTMLRepository()

    archive_context = ArchiveRAGContext()

    logger = logging.getLogger(
        "AutoSearch"
    )

    previous_level = logger.level

    logger.setLevel(
        logging.WARNING
    )

    try:
        result = _find_snapshot_case(
            repository=repository,
        )
    finally:
        logger.setLevel(
            previous_level
        )

    case = result["case"]

    print()
    print(
        "=" * 60
    )
    print(
        "R10.4 Snapshot Integration Discovery"
    )
    print(
        "=" * 60
    )
    print(
        f"Checked URLs              : "
        f"{result['checked_urls']}"
    )
    print(
        f"URLs with >= 2 Snapshots  : "
        f"{result['multi_snapshot_urls']}"
    )
    print(
        f"SnapshotDocument Success  : "
        f"{result['document_success']}"
    )
    print(
        f"SnapshotDocument Failures : "
        f"{result['document_failures']}"
    )
    print(
        f"Difference Comparisons    : "
        f"{result['difference_checked']}"
    )
    print(
        f"Changed Snapshot Cases    : "
        f"{result['changed_cases']}"
    )

    if case is None:
        _print_snapshot_error_summary(
            result["document_errors"]
        )

    assert case is not None, (
        "R10.4 Snapshot Integration could not "
        "find a real MongoDB Snapshot pair with "
        "different cleaned article content."
    )

    url = case["url"]

    historical_snapshot = (
        case["historical_snapshot"]
    )

    latest_snapshot = (
        case["latest_snapshot"]
    )

    historical_document = (
        case["historical_document"]
    )

    latest_document = (
        case["latest_document"]
    )

    difference = case["difference"]

    assert url

    assert (
        historical_document.url
        == url
    )

    assert (
        latest_document.url
        == url
    )

    assert (
        historical_document.snapshot_created_at
        != latest_document.snapshot_created_at
    )

    assert difference.has_changes

    assert (
        difference.added
        or difference.deleted
        or difference.modified
    )

    historical_context = (
        archive_context.build_difference_context(
            historical_snapshot=(
                historical_snapshot
            ),
            latest_snapshot=(
                latest_snapshot
            ),
        )
    )

    assert isinstance(
        historical_context,
        str,
    )

    assert historical_context.strip()

    assert (
        "Historical Snapshot Time:"
        in historical_context
    )

    assert (
        "Latest Snapshot Time:"
        in historical_context
    )

    latest_context = {
        "context_text": (
            "Latest Article Context"
        )
    }

    combined_context = (
        archive_context.combine(
            latest_context=latest_context,
            historical_context=historical_context,
        )
    )

    assert isinstance(
        combined_context,
        dict,
    )

    assert (
        "context_text"
        in combined_context
    )

    combined_text = (
        combined_context["context_text"]
    )

    assert (
        "[Historical Snapshot Context]"
        in combined_text
    )

    assert (
        historical_context
        in combined_text
    )

    print()
    print(
        "Selected URL:"
    )
    print(
        url
    )
    print()
    print(
        "Historical Snapshot:"
    )
    print(
        historical_document.snapshot_created_at
    )
    print(
        "Latest Snapshot:"
    )
    print(
        latest_document.snapshot_created_at
    )
    print()
    print(
        f"Added    : "
        f"{len(difference.added)}"
    )
    print(
        f"Deleted  : "
        f"{len(difference.deleted)}"
    )
    print(
        f"Modified : "
        f"{len(difference.modified)}"
    )
    print()
    print(
        "R10.4 Snapshot Integration: PASS"
    )


def test_r10_4_real_rag_integration():
    """
    驗證 Latest ChromaDB + Historical Snapshot
    → ArchiveRAGContext → RAGQuery → Groq。
    """

    repository = RawHTMLRepository()

    archive_context = ArchiveRAGContext()

    logger = logging.getLogger(
        "AutoSearch"
    )

    previous_level = logger.level

    logger.setLevel(
        logging.WARNING
    )

    try:
        result = _find_rag_case(
            repository=repository,
            archive_context=archive_context,
        )
    finally:
        logger.setLevel(
            previous_level
        )

    case = result["case"]

    print()
    print(
        "=" * 60
    )
    print(
        "R10.4 RAG Integration Discovery"
    )
    print(
        "=" * 60
    )
    print(
        f"Checked URLs             : "
        f"{result['checked_urls']}"
    )
    print(
        f"URLs with >= 2 Snapshots : "
        f"{result['multi_snapshot_urls']}"
    )
    print(
        f"Query Build Failures     : "
        f"{result['query_failures']}"
    )
    print(
        f"Retrieval Attempts       : "
        f"{result['retrieval_attempts']}"
    )
    print(
        f"Retrieval Success        : "
        f"{result['retrieval_success']}"
    )
    print(
        f"Empty Context            : "
        f"{result['empty_context']}"
    )
    print(
        f"Retrieval Failures       : "
        f"{result['retrieval_failures']}"
    )

    assert case is not None, (
        "R10.4 RAG Integration could not find "
        "a real MongoDB URL with multiple Snapshots "
        "and a non-empty context from the existing "
        "ChromaDB RAG retrieval."
    )

    url = case["url"]

    query = case["query"]

    latest_snapshot = (
        case["latest_snapshot"]
    )

    snapshots = case["snapshots"]

    latest_context = (
        case["latest_context"]
    )

    assert len(snapshots) >= (
        MIN_SNAPSHOT_COUNT
    )

    historical_snapshot = snapshots[1]

    combined_context = (
        archive_context.build(
            query=query,
            urls=[url],
            historical_snapshot=(
                historical_snapshot
            ),
            latest_snapshot=(
                latest_snapshot
            ),
        )
    )

    assert isinstance(
        combined_context,
        dict,
    )

    assert (
        "context_text"
        in combined_context
    )

    combined_text = (
        combined_context["context_text"]
    )

    assert combined_text.strip()

    assert (
        "[Historical Snapshot Context]"
        in combined_text
    )

    rag_query = RAGQuery()

    response = rag_query.run(
        query=query,
        urls=[url],
        historical_snapshot=(
            historical_snapshot
        ),
        latest_snapshot=(
            latest_snapshot
        ),
    )

    assert isinstance(
        response,
        dict,
    )

    assert "answer" in response

    assert "sources" in response

    answer = response["answer"]

    sources = response["sources"]

    assert isinstance(
        answer,
        str,
    )

    assert answer.strip()

    assert isinstance(
        sources,
        list,
    )

    assert sources

    print()
    print(
        "Selected URL:"
    )
    print(
        url
    )
    print()
    print(
        "Query:"
    )
    print(
        query
    )
    print()
    print(
        "Historical Snapshot:"
    )
    print(
        historical_snapshot.get(
            "created_at"
        )
    )
    print(
        "Latest Snapshot:"
    )
    print(
        latest_snapshot.get(
            "created_at"
        )
    )
    print()
    print(
        f"Latest Context Length   : "
        f"{len(latest_context.get('context_text', ''))}"
    )
    print(
        f"Combined Context Length : "
        f"{len(combined_text)}"
    )
    print(
        f"Sources                 : "
        f"{len(sources)}"
    )
    print()
    print(
        "R10.4 RAG Integration: PASS"
    )
    print()
    print(
        "Answer:"
    )
    print(
        answer
    )