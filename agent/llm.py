"""Gemini LLM + Embeddings client."""

from google import genai
from agent.config import settings
from agent.logger import get_logger
from agent.prompt import SYSTEM_PROMPT

log = get_logger(__name__)


class GeminiClient:
    """Wraps Gemini API for embeddings and generation."""

    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())
        log.info(f"Gemini ready | LLM={settings.GEMINI_MODEL} | Embed={settings.EMBED_MODEL}")


    def embed(self, text: str) -> list[float]:
        """Return embedding vector for text."""
        result = self._client.models.embed_content(model=settings.EMBED_MODEL, contents=text)
        return result.embeddings[0].values


    def ask(self, query: str, context: str, history_text: str = "") -> str:
        """Generate answer from context + pre-formatted history text."""
        prompt = f"{SYSTEM_PROMPT}\n{history_text}\nContext:\n{context}\n\nQuestion: {query}"
        response = self._client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        log.info(f"Generated {len(response.text)} chars | query: {query[:50]}")
        return response.text


