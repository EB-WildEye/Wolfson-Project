"""LanceDB vector store wrapper."""

import lancedb
from agent.config import settings
from agent.logger import get_logger
from agent.llm import GeminiClient

log = get_logger(__name__)


class VectorStore:
    """Manages LanceDB connection, search, and storage."""

    def __init__(self, llm: GeminiClient):
        self._db = lancedb.connect(str(settings.LANCEDB_PATH))
        self._llm = llm
        log.info(f"LanceDB connected | path={settings.LANCEDB_PATH}")


    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """Embed query and return top-k similar chunks."""
        table = self._db.open_table(settings.LANCEDB_TABLE)
        results = table.search(self._llm.embed(query)).limit(top_k).to_list()
        log.debug(f"Search returned {len(results)} results | query: {query[:40]}")
        return results


    def upsert(self, chunks: list[dict]):
        """Create/overwrite the documents table."""
        self._db.create_table(settings.LANCEDB_TABLE, chunks, mode="overwrite")
        log.info(f"Stored {len(chunks)} chunks in '{settings.LANCEDB_TABLE}'")


    def drop_table(self):
        """Drop the documents table."""
        try:
            self._db.drop_table(settings.LANCEDB_TABLE)
            log.warning(f"Dropped table '{settings.LANCEDB_TABLE}'")
        except Exception:
            log.info(f"Table '{settings.LANCEDB_TABLE}' does not exist, nothing to drop")


    def count(self) -> int:
        """Return number of rows in the table."""
        try:
            return self._db.open_table(settings.LANCEDB_TABLE).count_rows()
        except Exception:
            return 0
