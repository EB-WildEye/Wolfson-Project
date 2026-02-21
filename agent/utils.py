"""
agent/utils.py – Shared connections: Gemini client, LanceDB, MongoDB.

This is the single source of truth for all external service connections.
Every other module imports from here – no duplicate setup.
"""

import os
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient
import lancedb

load_dotenv()

# ── Gemini ────────────────────────────────────────────────────

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")


def embed_text(text: str) -> list[float]:
    """Turn a string into a 768-dim vector using Gemini embeddings."""
    result = gemini_client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


def ask_gemini(query: str, context: str) -> str:
    """Send query + retrieved context to Gemini, get answer back."""
    prompt = (
        "You are Gali (גלי), a helpful AI assistant for the gynecology department "
        "at Wolfson Medical Center (מרכז רפואי וולפסון).\n\n"
        "Rules:\n"
        "- ALWAYS respond in Hebrew (עברית).\n"
        "- Answer based ONLY on the context below.\n"
        "- If the context doesn't contain the answer, say so honestly.\n"
        "- Always recommend consulting a physician for medical decisions.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text


# ── LanceDB ──────────────────────────────────────────────────

LANCEDB_PATH = os.getenv("LANCEDB_PATH", "./lancedb_data")
lance_db = lancedb.connect(LANCEDB_PATH)


def search_docs(query: str, top_k: int = 4) -> list[dict]:
    """Embed the query and search LanceDB for similar chunks."""
    table = lance_db.open_table("documents")
    query_vec = embed_text(query)
    results = table.search(query_vec).limit(top_k).to_list()
    return results


# ── MongoDB (optional – works without it) ─────────────────────

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    mongo_client.admin.command("ping")  # test connection
    chat_db = mongo_client["gali"]
    history_col = chat_db["chat_history"]
    MONGO_AVAILABLE = True
    print("✅ MongoDB connected")
except Exception:
    MONGO_AVAILABLE = False
    print("⚠️  MongoDB not available – chat history disabled")


def save_message(session_id: str, role: str, content: str):
    """Save a single chat message to MongoDB (skips if Mongo is down)."""
    if not MONGO_AVAILABLE:
        return
    history_col.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
    })


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    """Get the last N messages for a session."""
    if not MONGO_AVAILABLE:
        return []
    cursor = history_col.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1},
    ).sort("_id", -1).limit(limit)
    messages = list(cursor)
    messages.reverse()  # oldest first
    return messages

