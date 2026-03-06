"""Gemini LLM + Embeddings client — uses native Chat API."""

import time
from google import genai
from google.genai import types
from agent.config import settings
from agent.logger import get_logger
from agent.prompt import SYSTEM_PROMPT

log = get_logger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 2  # seconds


class GeminiClient:
    """Wraps Gemini API for embeddings and chat generation."""

    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )
        log.info(f"Gemini ready | LLM={settings.GEMINI_MODEL} | Embed={settings.EMBED_MODEL}")


    def embed_text(self, text: str) -> list[float]:
        """Return embedding vector for a given text."""
        result = self._client.models.embed_content(model=settings.EMBED_MODEL, contents=text)
        return result.embeddings[0].values


    def generate_answer(self, query: str, context: str, history: list[dict] | None = None) -> str:
        """Generate a RAG answer using Gemini's native multi-turn chat.

        Args:
            query:   The user's current question.
            context: Retrieved RAG context to ground the answer.
            history: List of past messages as {"role": "user"|"model", "parts": [{"text": ...}]}.

        Returns:
            The model's text response.
        """
        # Build Gemini-native history from MongoDB messages
        gemini_history = []
        for msg in (history or []):
            gemini_history.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=msg["parts"][0]["text"])],
                )
            )

        # Create a chat session with system instructions + history
        chat = self._client.chats.create(
            model=settings.GEMINI_MODEL,
            config=self._config,
            history=gemini_history,
        )

        # Inject RAG context into the user message
        message = f"Context:\n{context}\n\nQuestion: {query}"

        # Retry with exponential backoff on transient errors
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = chat.send_message(message)
                log.info(f"Generated {len(response.text)} chars | query: {query[:50]}")
                return response.text
            except Exception as e:
                err_str = str(e)
                is_transient = any(k in err_str for k in ("503", "429", "UNAVAILABLE", "overloaded", "high demand"))

                if is_transient and attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** (attempt - 1))
                    log.warning(f"Gemini transient error (attempt {attempt}/{MAX_RETRIES}), retrying in {delay}s: {err_str[:120]}")
                    time.sleep(delay)
                else:
                    log.error(f"Gemini failed after {attempt} attempt(s): {err_str[:200]}")
                    raise
