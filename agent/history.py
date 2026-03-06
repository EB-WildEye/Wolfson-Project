"""MongoDB chat history manager with PII scrubbing."""

import re
from pymongo import MongoClient
from agent.config import settings
from agent.logger import get_logger

log = get_logger(__name__)

_PII_PATTERNS = [
    (re.compile(r"\b\d{9}\b"), "[ת.ז. הוסר]"),
    (re.compile(r"\b0[2-9]\d?-?\d{7}\b"), "[טלפון הוסר]"),
    (re.compile(r"\+972-?\d{1,2}-?\d{7}\b"), "[טלפון הוסר]"),
    (re.compile(r"\b\d{3}-?\d{7}\b"), "[טלפון הוסר]"),
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[אימייל הוסר]"),
]

HISTORY_LIMIT = 20


class ChatHistory:
    """Manages chat persistence and PII scrubbing."""

    def __init__(self):
        self._available = False
        try:
            self._client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
            self._client.admin.command("ping")
            db = self._client[settings.MONGO_DB_NAME]
            self._col = db["chat_history"]
            self._col.create_index("session_id")
            self._available = True
            log.info("MongoDB connected")
        except Exception as e:
            log.warning(f"MongoDB unavailable — history disabled: {e}")


    def save_conversation_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        """Atomically save both user and assistant messages."""
        if not self._available:
            return
        docs = [
            {"session_id": session_id, "role": "user", "content": self._remove_pii(user_msg)},
            {"session_id": session_id, "role": "assistant", "content": self._remove_pii(assistant_msg)},
        ]
        self._col.insert_many(docs)


    def check_connection(self):
        """Lightweight check that MongoDB is reachable."""
        if not self._available:
            raise ConnectionError("MongoDB not connected")
        self._client.admin.command("ping")


    def get_messages(self, session_id: str, limit: int = HISTORY_LIMIT) -> list[dict]:
        """Return last N messages for a session, oldest first."""
        if not self._available:
            return []
        cursor = (
            self._col.find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1})
            .sort("_id", -1)
            .limit(limit)
        )
        msgs = list(cursor)
        msgs.reverse()
        return msgs


    def get_chat_history(self, session_id: str) -> list[dict]:
        """Return chat history in Gemini-native format.

        Converts MongoDB messages to the format expected by Gemini's Chat API:
          [{"role": "user"|"model", "parts": [{"text": "..."}]}]
        """
        msgs = self.get_messages(session_id)
        history = []
        for msg in msgs:
            # MongoDB stores "assistant", Gemini expects "model"
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [{"text": msg["content"]}]})
        return history


    def _remove_pii(self, text: str) -> str:
        """Remove Israeli IDs, phone numbers, and emails."""
        for pattern, replacement in _PII_PATTERNS:
            if pattern.search(text):
                log.info(f"PII scrubbed: {replacement}")
                text = pattern.sub(replacement, text)
        return text
