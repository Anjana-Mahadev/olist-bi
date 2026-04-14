"""
Short-term conversation memory.

Keeps the last N question/answer turns per session in memory so that
follow-up questions ("what about by state?") can be resolved in context.
Sessions expire after a configurable TTL to prevent unbounded growth.
"""

import threading
import time
from collections import OrderedDict
from typing import Dict, List, Optional


MAX_TURNS = 5          # how many Q/A pairs to keep per session
SESSION_TTL = 1800     # seconds (30 min) before a session auto-expires
MAX_SESSIONS = 500     # cap to prevent unbounded memory growth


class _Turn:
    __slots__ = ("question", "sql", "answer")

    def __init__(self, question: str, sql: str, answer: str):
        self.question = question
        self.sql = sql
        self.answer = answer


class _Session:
    __slots__ = ("turns", "last_active")

    def __init__(self):
        self.turns: List[_Turn] = []
        self.last_active: float = time.time()

    def add_turn(self, question: str, sql: str, answer: str):
        self.turns.append(_Turn(question, sql, answer))
        if len(self.turns) > MAX_TURNS:
            self.turns = self.turns[-MAX_TURNS:]
        self.last_active = time.time()

    def to_history(self) -> List[Dict[str, str]]:
        return [
            {"question": t.question, "sql": t.sql, "answer": t.answer}
            for t in self.turns
        ]

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL


class ConversationMemory:
    """Thread-safe, in-memory conversation store keyed by session_id."""

    def __init__(self):
        self._sessions: OrderedDict[str, _Session] = OrderedDict()
        self._lock = threading.Lock()

    def _evict(self):
        """Remove expired sessions and cap total count."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]
        while len(self._sessions) > MAX_SESSIONS:
            self._sessions.popitem(last=False)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with self._lock:
            self._evict()
            session = self._sessions.get(session_id)
            if session is None or session.is_expired():
                return []
            return session.to_history()

    def add_turn(self, session_id: str, question: str, sql: str = "", answer: str = ""):
        with self._lock:
            self._evict()
            if session_id not in self._sessions:
                self._sessions[session_id] = _Session()
            self._sessions[session_id].add_turn(question, sql, answer)

    def clear_session(self, session_id: str):
        with self._lock:
            self._sessions.pop(session_id, None)


# Module-level singleton
conversation_memory = ConversationMemory()
