"""MongoDB chat history manager with PII scrubbing and summarization."""

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

SUMMARY_THRESHOLD = 10
RECENT_COUNT = 4


class ChatHistory:
    """Manages chat persistence, PII scrubbing, and cached summarization."""

    def __init__(self, llm=None):
        self._llm = llm
        self._available = False
        try:
            self._client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
            self._client.admin.command("ping")
            db = self._client[settings.MONGO_DB_NAME]
            self._col = db["chat_history"]
            self._summary_col = db["summary_cache"]
            self._available = True
            log.info("MongoDB connected")
        except Exception as e:
            log.warning(f"MongoDB unavailable — history disabled: {e}")


    def save(self, session_id: str, role: str, content: str):
        """Scrub PII then persist message."""
        if not self._available:
            return
        self._col.insert_one({"session_id": session_id, "role": role, "content": self._scrub_pii(content)})


    def get(self, session_id: str, limit: int = 20) -> list[dict]:
        """Return last N messages for a session, oldest first."""
        if not self._available:
            return []
        cursor = self._col.find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1}).sort("_id", -1).limit(limit)
        msgs = list(cursor)
        msgs.reverse()
        return msgs


    def get_condensed(self, session_id: str) -> str:
        """Return history as text — uses cached summary if available."""
        msgs = self.get(session_id)
        if not msgs:
            return ""

        if len(msgs) <= SUMMARY_THRESHOLD:
            lines = [f"{'Patient' if m['role']=='user' else 'Gali'}: {m['content']}" for m in msgs]
            return "\n### Conversation History:\n" + "\n".join(lines) + "\n"

        older = msgs[:-RECENT_COUNT]
        recent = msgs[-RECENT_COUNT:]

        summary = self._get_cached_summary(session_id, len(older))
        recent_lines = [f"{'Patient' if m['role']=='user' else 'Gali'}: {m['content']}" for m in recent]
        return f"\n### Summary of earlier conversation:\n{summary}\n\n### Recent messages:\n" + "\n".join(recent_lines) + "\n"


    def _get_cached_summary(self, session_id: str, msg_count: int) -> str:
        """Return cached summary or generate + cache a new one."""
        if self._available:
            cached = self._summary_col.find_one({"session_id": session_id})
            if cached and cached.get("msg_count") == msg_count:
                log.debug("Using cached summary")
                return cached["summary"]

        summary = self._summarize_messages(session_id, msg_count)

        if self._available:
            self._summary_col.update_one(
                {"session_id": session_id},
                {"$set": {"summary": summary, "msg_count": msg_count}},
                upsert=True,
            )
            log.info(f"Summary cached | session={session_id} | msgs={msg_count}")

        return summary


    def _summarize_messages(self, session_id: str, count: int) -> str:
        """Summarize older messages via Gemini."""
        if not self._llm:
            return "[summary unavailable]"
        msgs = self.get(session_id, limit=count + RECENT_COUNT)
        older = msgs[:count]
        text = "\n".join(f"{m['role']}: {m['content']}" for m in older)
        prompt = (
            "Summarize this conversation in 2-3 bullet points. "
            "Keep: patient name, medical topics, key decisions. "
            "Remove: greetings, disclaimers, filler.\n\n" + text
        )
        response = self._llm._client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        log.info(f"Generated summary for {count} messages")
        return response.text


    def _scrub_pii(self, text: str) -> str:
        """Remove Israeli IDs, phone numbers, and emails."""
        for pattern, replacement in _PII_PATTERNS:
            if pattern.search(text):
                log.info(f"PII scrubbed: {replacement}")
                text = pattern.sub(replacement, text)
        return text

