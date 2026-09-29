"""
tests/V8_0/test_r10_6_ui.py

AutoSearch V7

R10.6

Article Archive Chatbot UI Test

驗證：

    1. Robot UI 存在
    2. Chat Message List 存在
    3. Input 存在
    4. Send Button 存在
    5. Article URL 綁定
    6. Snapshot Version 綁定
    7. /archive/chat API 呼叫
    8. Latest / Historical Version 傳遞
    9. Answer / Sources 顯示
    10. Error Handling
"""

from pathlib import Path


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "archive"
    / "viewer.html"
)


def _read_template():
    assert TEMPLATE_PATH.exists()

    return TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )


def test_archive_chat_ui_exists():
    html = _read_template()

    assert (
        'class="archive-chat"'
        in html
    )

    assert (
        "Article Archive Robot"
        in html
    )


def test_archive_chat_messages_exists():
    html = _read_template()

    assert (
        'id="archive-chat-messages"'
        in html
    )

    assert (
        'class="archive-chat-messages"'
        in html
    )


def test_archive_chat_input_exists():
    html = _read_template()

    assert (
        'id="archive-chat-input"'
        in html
    )

    assert (
        'class="archive-chat-input"'
        in html
    )


def test_archive_chat_send_button_exists():
    html = _read_template()

    assert (
        'id="archive-chat-send"'
        in html
    )

    assert (
        'class="archive-chat-send"'
        in html
    )

    assert (
        'type="button"'
        in html
    )


def test_archive_chat_status_exists():
    html = _read_template()

    assert (
        'id="archive-chat-status"'
        in html
    )


def test_archive_chat_article_url_binding():
    html = _read_template()

    assert (
        "const articleUrl = {{ url | tojson }};"
        in html
    )


def test_archive_chat_version_binding():
    html = _read_template()

    assert (
        "const selectedVersion = "
        "{{ selected_version | tojson }};"
        in html
    )


def test_archive_chat_api_request():
    html = _read_template()

    assert (
        'fetch('
        in html
    )

    assert (
        '"/archive/chat"'
        in html
    )

    assert (
        'method: "POST"'
        in html
    )

    assert (
        '"Content-Type":'
        in html
    )

    assert (
        '"application/json"'
        in html
    )


def test_archive_chat_request_payload():
    html = _read_template()

    assert (
        "url: articleUrl"
        in html
    )

    assert (
        "query: query"
        in html
    )

    assert (
        "version:"
        in html
    )

    assert (
        "selectedVersion || null"
        in html
    )


def test_archive_chat_response_handling():
    html = _read_template()

    assert (
        "data.answer"
        in html
    )

    assert (
        "data.sources"
        in html
    )

    assert (
        "addMessage("
        in html
    )


def test_archive_chat_error_handling():
    html = _read_template()

    assert (
        "response.ok"
        in html
    )

    assert (
        "Archive Chat failed."
        in html
    )

    assert (
        "Robot Error:"
        in html
    )

    assert (
        'setStatus('
        in html
    )


def test_archive_chat_enter_to_send():
    html = _read_template()

    assert (
        'event.key === "Enter"'
        in html
    )

    assert (
        "sendMessage()"
        in html
    )


def test_archive_chat_shift_enter_newline():
    html = _read_template()

    assert (
        "!event.shiftKey"
        in html
    )


def test_archive_chat_loading_state():
    html = _read_template()

    assert (
        "sendButton.disabled ="
        in html
    )

    assert (
        "inputElement.disabled ="
        in html
    )

    assert (
        '"Thinking..."'
        in html
    )

    assert (
        '"Ready"'
        in html
    )


def test_archive_chat_sources_rendering():
    html = _read_template()

    assert (
        "Array.isArray(sources)"
        in html
    )

    assert (
        "chat-sources"
        in html
    )

    assert (
        "引用來源"
        in html
    )


def test_archive_chat_mobile_ui():
    html = _read_template()

    assert (
        "@media (max-width: 768px)"
        in html
    )

    assert (
        ".archive-chat-input-area"
        in html
    )

    assert (
        ".archive-chat-send"
        in html
    )