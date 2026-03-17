"""MongoDB session store — ephemeral chat history (NOT for RAG).

MongoDB stores conversation turns only (user ↔ assistant messages).
All session data is deleted after 24 hours by the Cleanup Lambda.
RAG retrieval is handled by LanceDB in the Chat service — never here.

Connection is lazy-initialized and cached across warm Lambda invocations.
"""

from datetime import datetime, timedelta, timezone
import logging

from pymongo import MongoClient
from pymongo.collection import Collection

from shared.config import get_mongo_uri
from shared.pii import remove_pii

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module state (persists across warm Lambda invocations)
# ---------------------------------------------------------------------------
_client: MongoClient | None = None
_col: Collection | None = None

HISTORY_LIMIT = 20


def get_collection() -> Collection:
    """Return the ``chat_history`` collection (session store only), lazy-connecting."""
    global _client, _col
    if _col is not None:
        return _col

    uri = get_mongo_uri()
    _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    _client.admin.command("ping")
    db = _client["gali"]
    _col = db["chat_history"]
    _col.create_index("session_id")
    logger.info("MongoDB connected (session store)")
    return _col


# ---------------------------------------------------------------------------
# Session history CRUD — plain message storage, no vectors, no RAG
# ---------------------------------------------------------------------------

def save_turn(session_id: str, user_msg: str, assistant_msg: str) -> None:
    """Scrub PII then insert both the user and assistant messages."""
    col = get_collection()
    now = datetime.now(timezone.utc)
    docs = [
        {
            "session_id": session_id,
            "role": "user",
            "content": remove_pii(user_msg),
            "created_at": now,
        },
        {
            "session_id": session_id,
            "role": "assistant",
            "content": remove_pii(assistant_msg),
            "created_at": now,
        },
    ]
    col.insert_many(docs)
    logger.debug("Saved turn for session %s", session_id)


def get_messages(session_id: str, limit: int = HISTORY_LIMIT) -> list[dict]:
    """Return the last *limit* session messages, oldest-first.

    Returns a plain list: ``[{"role": ..., "content": ...}]``.
    No vectors, no embeddings — just conversation text.
    """
    col = get_collection()
    cursor = (
        col.find(
            {"session_id": session_id},
            {"_id": 0, "role": 1, "content": 1},
        )
        .sort("_id", -1)
        .limit(limit)
    )
    msgs = list(cursor)
    msgs.reverse()
    return msgs


def get_chat_history(session_id: str) -> list[dict]:
    """Return session messages as a Gemini-format list.

    This is **conversation memory** — it gives Gemini the past turns so it
    can maintain context across messages.  It is NOT RAG retrieval;
    RAG context comes from LanceDB vector search in the Chat service.

    Returns ``[{"role": "user"|"model", "parts": [{"text": ...}]}]``.
    """
    msgs = get_messages(session_id)
    history = []
    for msg in msgs:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [{"text": msg["content"]}]})
    return history


def delete_old_messages(hours: int = 24) -> int:
    """Delete ephemeral session messages older than *hours*. Returns count."""
    col = get_collection()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = col.delete_many({"created_at": {"$lt": cutoff}})
    logger.info("Deleted %d messages older than %dh", result.deleted_count, hours)
    return result.deleted_count


def check_connection() -> None:
    """Ping MongoDB to verify the connection is alive."""
    if _client is None:
        get_collection()
    _client.admin.command("ping")
