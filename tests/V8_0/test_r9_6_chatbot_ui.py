"""
tests/V8_0/test_r9_6_chatbot_ui.py

AutoSearch V7

R9.6 Chatbot UI Test
"""

import re
import unittest
from pathlib import Path


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "archive"
    / "search.html"
)


class TestR96ChatbotUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not TEMPLATE_PATH.exists():
            raise FileNotFoundError(
                f"Template not found: {TEMPLATE_PATH}"
            )

        cls.html = TEMPLATE_PATH.read_text(
            encoding="utf-8"
        )

    def test_chatbot_structure(self):
        required_ids = [
            "chatbot-toggle",
            "chatbot-panel",
            "chatbot-scope",
            "chatbot-messages",
            "chatbot-input",
            "chatbot-send",
        ]

        for element_id in required_ids:
            with self.subTest(element_id=element_id):
                self.assertIn(
                    f'id="{element_id}"',
                    self.html,
                )

    def test_chatbot_api_configuration(self):
        self.assertIn(
            'const RAG_API =',
            self.html,
        )

        self.assertRegex(
            self.html,
            r'const\s+RAG_API\s*=\s*["\']/rag/query["\'];',
        )

    def test_chatbot_scope_default(self):
        self.assertIn(
            "Scope: All Archive",
            self.html,
        )

        self.assertIn(
            "let archiveSearchScope = null;",
            self.html,
        )

    def test_chatbot_scope_functions(self):
        required_functions = [
            "getArchiveSearchScope",
            "updateArchiveSearchScope",
            "updateChatbotScopeDisplay",
        ]

        for function_name in required_functions:
            with self.subTest(function_name=function_name):
                self.assertRegex(
                    self.html,
                    rf"function\s+{function_name}\s*\(",
                )

    def test_chatbot_message_functions(self):
        required_functions = [
            "toggleChatbot",
            "handleChatInputKeydown",
            "appendChatMessage",
            "sendChatMessage",
        ]

        for function_name in required_functions:
            with self.subTest(function_name=function_name):
                self.assertRegex(
                    self.html,
                    rf"function\s+{function_name}\s*\(",
                )

    def test_chatbot_request_contains_query_and_urls(self):
        self.assertIn(
            "const requestBody =",
            self.html,
        )

        self.assertRegex(
            self.html,
            r"query:\s*query",
        )

        self.assertRegex(
            self.html,
            r"urls:\s*getArchiveSearchScope\(\)",
        )

    def test_chatbot_post_request(self):
        self.assertRegex(
            self.html,
            r'fetch\(\s*RAG_API',
        )

        self.assertRegex(
            self.html,
            r'method:\s*["\']POST["\']',
        )

        self.assertIn(
            '"Content-Type"',
            self.html,
        )

        self.assertIn(
            "application/json",
            self.html,
        )

        self.assertIn(
            "JSON.stringify",
            self.html,
        )

    def test_chatbot_answer_display(self):
        self.assertRegex(
            self.html,
            r'\[\s*"answer"\s*\]',
        )

        self.assertIn(
            "appendChatMessage(",
            self.html,
        )

        self.assertIn(
            "目前沒有可用的回答。",
            self.html,
        )

    def test_chatbot_sources_display(self):
        required_source_fields = [
            "source_index",
            "title",
            "url",
        ]

        for field in required_source_fields:
            with self.subTest(field=field):
                self.assertIn(
                    f'"{field}"',
                    self.html,
                )

        self.assertIn(
            "Sources",
            self.html,
        )

    def test_chatbot_error_handling(self):
        self.assertIn(
            "RAG API request failed",
            self.html,
        )

        self.assertIn(
            "RAG API 回傳的不是 JSON。",
            self.html,
        )

        self.assertIn(
            "RAG API JSON 格式錯誤。",
            self.html,
        )

        self.assertIn(
            "Chatbot failed:",
            self.html,
        )

    def test_chatbot_enter_to_send(self):
        self.assertIn(
            'event.key === "Enter"',
            self.html,
        )

        self.assertIn(
            "sendChatMessage();",
            self.html,
        )

    def test_chatbot_scope_in_search_flow(self):
        self.assertIn(
            "loadFullSearchScope",
            self.html,
        )

        self.assertIn(
            "updateArchiveSearchScope",
            self.html,
        )

        self.assertRegex(
            self.html,
            r"if\s*\(\s*isNewSearch\s*\)",
        )

    def test_chatbot_scope_preserved_on_page_navigation(self):
        self.assertRegex(
            self.html,
            r"searchArchive\(\$\{page\s*-\s*1\},\s*false\)",
        )

        self.assertRegex(
            self.html,
            r"searchArchive\(\$\{page\s*\+\s*1\},\s*false\)",
        )

    def test_chatbot_scope_reset(self):
        reset_section = re.search(
            r"function\s+resetSearch\s*\(.*?\n\}",
            self.html,
            re.DOTALL,
        )

        self.assertIsNotNone(
            reset_section,
        )

        self.assertRegex(
            reset_section.group(0),
            r"archiveSearchScope\s*=\s*null\s*;",
        )

        self.assertRegex(
            reset_section.group(0),
            r"updateChatbotScopeDisplay\s*\(\s*\)\s*;",
        )


if __name__ == "__main__":
    unittest.main()