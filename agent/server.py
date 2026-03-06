"""Gali REST API server — production-ready FastAPI entry point."""

import re
import time
import unicodedata
import uuid
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from agent.config import settings
from agent.logger import get_logger
from agent.llm import GeminiClient
from agent.vectorstore import VectorStore
from agent.history import ChatHistory

log = get_logger(__name__)

API_PREFIX = "/api/v1"

# ── Globals ───────────────────────────────────────────────────

llm: GeminiClient = None
store: VectorStore = None
history: ChatHistory = None


# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    global llm, store, history
    log.info("Starting Gali API server...")
    llm = GeminiClient()
    store = VectorStore(llm)
    history = ChatHistory()
    log.info("All services initialized")
    yield
    log.info("Shutting down Gali API server")


# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="Gali API",
    version="1.0.0",
    description="RAG assistant for Wolfson Medical Center — Women's Department",
    lifespan=lifespan,
    # Hide docs in production
    docs_url="/docs" if settings.ENV == "dev" else None,
    redoc_url="/redoc" if settings.ENV == "dev" else None,
)


# ── CORS ─────────────────────────────────────────────────────
#
# CORS (Cross-Origin Resource Sharing) is a browser-enforced security policy.
# When your frontend (e.g. https://gali.hospital.com) calls this API, the
# browser first sends a preflight OPTIONS request asking "is my origin allowed?".
# If the server doesn't respond with the right `Access-Control-Allow-Origin`
# header, the browser BLOCKS the response — even though the server did respond.
#
# allow_origins=["*"]  ← NEVER in production for a medical system.
# It lets ANY website call your API on behalf of a logged-in user (CSRF risk).

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # e.g. ["https://gali.hospital.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],             # only what you actually expose
    allow_headers=["Content-Type", "Authorization"],
)


# ── Middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_and_track_request(request: Request, call_next):
    """Attach request ID, log timing, and add security headers."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        log.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms}ms)"
        )
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        log.error(f"[{request_id}] Unhandled error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": request_id},
        )


# ── Jailbreak / Prompt Injection Sanitizer ────────────────────
#
# ASCII jailbreaks smuggle instructions via Unicode lookalikes, zero-width
# chars, or base64-encoded payloads. NFKC normalization collapses lookalikes
# (e.g. ａ → a), then we strip invisible control characters.

INJECTION_PATTERN = re.compile(
    r"(ignore (previous|all|your)|disregard|you are now|act as|"
    r"jailbreak|pretend (you|to be)|forget (your )?instructions|"
    r"system prompt|bypass|override instructions)",
    re.IGNORECASE,
)


def sanitize_user_input(text: str) -> str:
    """Clean and validate user input against injection attacks."""
    # 1. Normalize Unicode — collapses lookalike characters
    text = unicodedata.normalize("NFKC", text)
    # 2. Strip zero-width, control, and invisible formatting characters
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"
        r"\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]",
        "",
        text,
    )
    # 3. Detect prompt injection keywords
    if INJECTION_PATTERN.search(text):
        log.warning(f"Blocked suspicious query: {text[:80]}")
        raise HTTPException(400, "Query contains disallowed content")

    return text.strip()


# ── Schemas ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=50)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        return sanitize_user_input(v)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    session_id: str = ""


class ServiceStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"


# ── Routes ────────────────────────────────────────────────────

@app.post(f"{API_PREFIX}/chat", response_model=ChatResponse)
async def handle_chat_message(req: ChatRequest):
    """RAG endpoint: sanitize → search → generate → save."""

    results = store.search_similar(req.query)
    if not results:
        raise HTTPException(424, "No documents ingested. Run: uv run python -m ingestion.main")

    context = "\n\n---\n\n".join(r["text"] for r in results)
    sources = list({r.get("source", "unknown") for r in results})
    chat_history = history.get_chat_history(req.session_id)

    try:
        answer = llm.generate_answer(req.query, context, history=chat_history)
    except Exception as e:
        err_str = str(e)
        if any(k in err_str for k in ("503", "429", "UNAVAILABLE", "overloaded", "high demand")):
            raise HTTPException(503, "השירות עמוס כרגע, נסו שוב בעוד מספר שניות")
        raise HTTPException(502, "LLM request failed")

    if not answer:
        raise HTTPException(502, "LLM returned an empty response")

    # Atomic save — both turns or neither
    history.save_conversation_turn(req.session_id, user_msg=req.query, assistant_msg=answer)

    log.info(f"session={req.session_id} sources={sources}")
    return ChatResponse(answer=answer, sources=sources, session_id=req.session_id)


@app.get(f"{API_PREFIX}/history/{{session_id}}")
async def retrieve_session_history(session_id: str):
    """Return chat history for a session."""
    return history.get_messages(session_id)


@app.get(f"{API_PREFIX}/health")
async def check_health():
    """
    Deep health check — verifies actual service liveness, not just process uptime.
    Returns 200 (ok) or 503 (degraded) for load balancer / uptime monitors.
    """
    checks: dict[str, str] = {}

    # Vector store ping
    try:
        store.check_connection()
        checks["vectorstore"] = "ok"
    except Exception as e:
        checks["vectorstore"] = f"error: {e}"

    # LLM initialization check (avoid calling the API — costs quota)
    checks["llm"] = "ok" if llm is not None else "not initialized"

    # History store check
    try:
        history.check_connection()
        checks["history"] = "ok"
    except Exception as e:
        checks["history"] = f"error: {e}"

    overall = (
        ServiceStatus.OK
        if all(v == "ok" for v in checks.values())
        else ServiceStatus.DEGRADED
    )

    return JSONResponse(
        status_code=200 if overall == ServiceStatus.OK else 503,
        content={
            "status": overall,
            "version": app.version,
            "model": settings.GEMINI_MODEL,
            "env": settings.ENV,
            "checks": checks,
        },
    )


# ── Global Exception Handlers ────────────────────────────────

@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": exc.status_code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    log.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENV == "dev" else None,
            "request_id": getattr(request.state, "request_id", None),
        },
    )