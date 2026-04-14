"""Ingestion CLI — reads PDFs/CSVs, cleans, embeds, stores in LanceDB.

Usage:
    python -m ingestion.main              # Normal ingestion
    python -m ingestion.main --drop       # Drop table, re-ingest
    python -m ingestion.main --purge      # Drop table + clear cache, full re-ingest
    python -m ingestion.main --drop-only  # Drop table and exit
"""

import re
import sys
import glob
import time
import json
import hashlib
import argparse
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.config import settings
from agent.logger import get_logger
from agent.llm import GeminiClient
from agent.vectorstore import VectorStore

log = get_logger(__name__)

CACHE_FILE = settings.DATA_DIR / ".ingestion_cache.json"


def parse_cli_args() -> argparse.Namespace:
    """Parse CLI arguments for the ingestion pipeline."""
    parser = argparse.ArgumentParser(prog="ingestion", description="Gali — Ingest documents into LanceDB.")
    parser.add_argument("--drop", action="store_true", help="Drop table before ingesting.")
    parser.add_argument("--purge", action="store_true", help="Drop table + clear hash cache, full re-ingest.")
    parser.add_argument("--drop-only", action="store_true", help="Drop table and exit.")
    return parser.parse_args()


class Ingestor:
    """Reads documents, cleans text, chunks, embeds, and stores."""

    def __init__(self):
        self._llm = GeminiClient()
        self._store = VectorStore(self._llm)
        self._cache = self._load_hash_cache()


    def ingest(self, drop=False, purge=False, drop_only=False):
        """Run the full ingestion pipeline with CLI flag support."""
        t_start = time.perf_counter()

        if drop or purge or drop_only:
            self._store.drop_table()

        if purge and CACHE_FILE.exists():
            CACHE_FILE.unlink()
            self._cache = {}
            log.warning("Hash cache cleared")

        if drop_only:
            log.info("--drop-only: Table dropped. Exiting.")
            return

        log.info(f"Existing rows: {self._store.count_rows()}")
        chunks, skipped = [], 0

        for path in glob.glob(str(settings.DATA_DIR / "*.pdf")) + glob.glob(str(settings.DATA_DIR / "*.csv")):
            name = Path(path).name
            file_hash = self._compute_file_hash(path)

            if file_hash == self._cache.get(name):
                log.info(f"Skipping (unchanged): {name}")
                skipped += 1
                continue

            log.info(f"Processing: {name}")
            text = self._extract_pdf_text(path) if path.endswith(".pdf") else self._extract_csv_text(path)
            file_chunks = self._split_into_chunks(text, name)
            chunks.extend(file_chunks)
            self._cache[name] = file_hash
            log.info(f"  → {len(file_chunks)} chunks from {len(text)} chars")

        if not chunks:
            log.info(f"Nothing to ingest ({skipped} files skipped)")
            self._save_hash_cache()
            return

        log.info(f"Embedding {len(chunks)} chunks...")
        for i, c in enumerate(chunks):
            c["vector"] = self._llm.embed_text(c["text"])
            if (i + 1) % 10 == 0:
                log.info(f"  Embedded {i+1}/{len(chunks)}")

        store_mode = "overwrite" if (drop or purge) else "append"
        self._store.store_chunks(chunks, mode=store_mode)
        self._save_hash_cache()

        elapsed = round(time.perf_counter() - t_start, 1)
        log.info(f"Done | {len(chunks)} chunks stored | {skipped} skipped | {elapsed}s")


    def _extract_pdf_text(self, path: str) -> str:
        """Extract text from PDF with table detection."""
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                for t in (page.extract_tables() or []):
                    rows = [" | ".join(str(c or "") for c in r) for r in t if any(c for c in r)]
                    parts.append("\n".join(rows))
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    parts.append(text)
        return self._normalize_text("\n\n".join(parts))


    def _extract_csv_text(self, path: str) -> str:
        """Read CSV file and return cleaned text."""
        with open(path, "r", encoding="utf-8") as f:
            return self._normalize_text(f.read())


    def _normalize_text(self, text: str) -> str:
        """Normalize whitespace and remove junk characters."""
        text = text.replace("\f", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n\s*[▪•●▸]\s*", "\n", text)
        return "\n".join(l.strip() for l in text.split("\n")).strip()


    def _split_into_chunks(self, text: str, source: str) -> list[dict]:
        """Split text into overlapping chunks for embedding."""
        chunks, start = [], 0
        while start < len(text):
            piece = text[start:start + settings.CHUNK_SIZE].strip()
            if piece:
                chunks.append({"text": piece, "source": source})
            start += settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
        return chunks


    def _compute_file_hash(self, path: str) -> str:
        """Compute SHA-256 hash of file contents for change detection."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                h.update(block)
        return h.hexdigest()[:16]


    def _load_hash_cache(self) -> dict:
        """Load file hash cache from disk."""
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text())
        return {}


    def _save_hash_cache(self):
        """Save file hash cache to disk."""
        CACHE_FILE.write_text(json.dumps(self._cache, indent=2))


if __name__ == "__main__":
    args = parse_cli_args()
    Ingestor().ingest(drop=args.drop, purge=args.purge, drop_only=args.drop_only)
