"""
ingestion/main.py – Reads PDFs & CSVs from ingestion/data/,
chunks the text, embeds with Gemini, and stores in LanceDB.

Run:
    cd Gali/
    uv run python -m ingestion.main
"""

import os
import sys
import glob
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader

# Add project root so we can import agent.utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.utils import embed_text, lance_db  # noqa: E402

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"


# ── File Readers ──────────────────────────────────────────────

def read_pdf(path: str) -> str:
    """Extract all text from a PDF."""
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_csv(path: str) -> str:
    """Read a CSV as raw text (each row becomes a searchable chunk)."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── Chunking ──────────────────────────────────────────────────

def chunk_text(text: str, source: str, size: int = 800, overlap: int = 200) -> list[dict]:
    """Split text into overlapping chunks with source metadata."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        piece = text[start:end].strip()
        if piece:
            chunks.append({"text": piece, "source": source})
        start += size - overlap
    return chunks


# ── Main ──────────────────────────────────────────────────────

def run():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    for pdf in glob.glob(str(DATA_DIR / "*.pdf")):
        print(f"� Loading: {os.path.basename(pdf)}")
        text = read_pdf(pdf)
        all_chunks.extend(chunk_text(text, os.path.basename(pdf)))

    for csv in glob.glob(str(DATA_DIR / "*.csv")):
        print(f"📊 Loading: {os.path.basename(csv)}")
        text = read_csv(csv)
        all_chunks.extend(chunk_text(text, os.path.basename(csv)))

    if not all_chunks:
        print("⚠️  No PDF/CSV files found in ingestion/data/")
        return

    print(f"✂️  {len(all_chunks)} chunks created")

    # Embed each chunk
    print("🔄 Embedding with Gemini...")
    for i, chunk in enumerate(all_chunks):
        chunk["vector"] = embed_text(chunk["text"])
        if (i + 1) % 10 == 0:
            print(f"   Embedded {i + 1}/{len(all_chunks)}")

    # Store in LanceDB (overwrites existing table)
    lance_db.create_table("documents", all_chunks, mode="overwrite")
    print(f"✅ Stored {len(all_chunks)} chunks in LanceDB")


if __name__ == "__main__":
    run()
