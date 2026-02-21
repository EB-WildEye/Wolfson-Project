"""
agent/main.py – FastAPI backend for Gali.

Endpoints:
    POST /chat          → Send a question, get a RAG answer
    GET  /history/{id}  → Get chat history for a session
    GET  /health        → Health check

Run:
    cd Gali/
    uv run uvicorn agent.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.utils import search_docs, ask_gemini, save_message, get_history

app = FastAPI(title="Gali API", version="0.1.0")


# ── Schemas ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


# ── Routes ────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Main RAG endpoint: retrieve → generate → save."""
    # 1. Search LanceDB for relevant chunks
    try:
        results = search_docs(req.query)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="No documents ingested yet. Run: uv run python -m ingestion.main",
        )

    # 2. Build context from results
    context = "\n\n---\n\n".join(r["text"] for r in results)
    sources = list(set(r.get("source", "unknown") for r in results))

    # 3. Ask Gemini
    answer = ask_gemini(req.query, context)

    # 4. Save to MongoDB
    save_message(req.session_id, "user", req.query)
    save_message(req.session_id, "assistant", answer)

    return ChatResponse(answer=answer, sources=sources)


@app.get("/history/{session_id}")
def history(session_id: str):
    """Return chat history for a given session."""
    return get_history(session_id)


@app.get("/health")
def health():
    """Simple health check."""
    return {"status": "ok"}
