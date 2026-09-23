"""
retrieval_context.py

AutoSearch V5

Retrieval Context

功能：

1. 管理可重用的 requests.Session
2. 使用 Thread-local 避免多執行緒直接共用同一 Session
3. 讓同一 Worker 可以重複使用 Session
4. 支援不同 Strategy 使用獨立 Session
5. 統一管理 Session cleanup
"""

from __future__ import annotations

import threading
from typing import Dict, List

import requests


class RetrievalContext:
    """
    管理一次 Resource Retrieval 工作期間可重用的 requests.Session。

    Session 以 thread + strategy 為單位建立與重用。
    """

    def __init__(self):
        self._local = threading.local()
        self._sessions: List[requests.Session] = []
        self._lock = threading.Lock()

    def _get_session_store(
        self,
    ) -> Dict[str, requests.Session]:
        """
        取得目前 Thread 的 Session store。
        """

        if not hasattr(self._local, "sessions"):
            self._local.sessions = {}

        return self._local.sessions

    def get_session(
        self,
        strategy: str = "http",
    ) -> requests.Session:
        """
        取得目前 Thread 對應 Strategy 的可重用 Session。

        同一 Thread + 同一 Strategy：
            → 重複使用同一 Session

        不同 Thread：
            → 使用不同 Session
        """

        sessions = self._get_session_store()

        if strategy not in sessions:
            session = requests.Session()

            sessions[strategy] = session

            with self._lock:
                self._sessions.append(session)

        return sessions[strategy]

    def close(self) -> None:
        """
        關閉 Context 管理的所有 Session。
        """

        with self._lock:
            sessions = list(self._sessions)
            self._sessions.clear()

        for session in sessions:
            try:
                session.close()
            except Exception:
                pass

        if hasattr(self._local, "sessions"):
            self._local.sessions.clear()

    def __enter__(self) -> "RetrievalContext":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()