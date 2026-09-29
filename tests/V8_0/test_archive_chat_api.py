"""
tests/V8_0/test_archive_chat_api.py

AutoSearch V7

R10.5

Article Archive Chat API Test
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.archive_chat import (
    get_archive_chat_service,
)


client = TestClient(app)


@pytest.fixture
def mock_service():
    service = MagicMock()

    service.run.return_value = {
        "answer": "這是測試回答。",
        "sources": [
            {
                "url": "https://example.com/article",
            }
        ],
    }

    return service


def test_archive_chat_router_registered():
    paths = app.openapi()["paths"]

    assert "/archive/chat" in paths

    assert "post" in paths[
        "/archive/chat"
    ]


def test_archive_chat_success(
    monkeypatch,
    mock_service,
):
    monkeypatch.setattr(
        "api.routes.archive_chat.get_archive_chat_service",
        lambda: mock_service,
    )

    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
            "query": "這篇文章的重點是什麼？",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "這是測試回答。"

    assert data["sources"] == [
        {
            "url": "https://example.com/article",
        }
    ]

    mock_service.run.assert_called_once_with(
        url="https://example.com/article",
        query="這篇文章的重點是什麼？",
        version=None,
    )


def test_archive_chat_with_version(
    monkeypatch,
    mock_service,
):
    monkeypatch.setattr(
        "api.routes.archive_chat.get_archive_chat_service",
        lambda: mock_service,
    )

    version = "2026-09-23T12:31:33.954000+00:00"

    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
            "query": "這個版本和最新版本有什麼差異？",
            "version": version,
        },
    )

    assert response.status_code == 200

    mock_service.run.assert_called_once_with(
        url="https://example.com/article",
        query="這個版本和最新版本有什麼差異？",
        version=version,
    )


def test_archive_chat_missing_url():
    response = client.post(
        "/archive/chat",
        json={
            "query": "這篇文章的重點是什麼？",
        },
    )

    assert response.status_code == 422


def test_archive_chat_empty_url():
    response = client.post(
        "/archive/chat",
        json={
            "url": "   ",
            "query": "這篇文章的重點是什麼？",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Article URL is required."
    )


def test_archive_chat_missing_query():
    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
        },
    )

    assert response.status_code == 422


def test_archive_chat_empty_query():
    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
            "query": "   ",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "User query is required."
    )


def test_archive_chat_service_value_error(
    monkeypatch,
):
    service = MagicMock()

    service.run.side_effect = ValueError(
        "Snapshot not found."
    )

    monkeypatch.setattr(
        "api.routes.archive_chat.get_archive_chat_service",
        lambda: service,
    )

    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
            "query": "歷史版本是什麼？",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Snapshot not found."
    )


def test_archive_chat_service_exception(
    monkeypatch,
):
    service = MagicMock()

    service.run.side_effect = Exception(
        "Test failure."
    )

    monkeypatch.setattr(
        "api.routes.archive_chat.get_archive_chat_service",
        lambda: service,
    )

    response = client.post(
        "/archive/chat",
        json={
            "url": "https://example.com/article",
            "query": "測試問題",
        },
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Archive Chat failed."
    )


