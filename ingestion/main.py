"""
ingestion/main.py – Reads PDFs & CSVs from ingestion/data/,
cleans text (with table detection), embeds with Gemini, stores in LanceDB.

Run:
    cd Gali/
    uv run python -m ingestion.main
"""

import os
import re
import sys
import glob
from pathlib import Path

from dotenv import load_dotenv
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.utils import embed_text, lance_db  # noqa: E402

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"


# ── Text Cleaning ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalize whitespace and remove junk from extracted text."""
    text = text.replace("\f", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)       # collapse blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)        # normalize spaces
    text = re.sub(r"\n\s*[▪•●▸]\s*", "\n", text)  # clean bullet chars
    lines = [l.strip() for l in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def table_to_text(table: list[list]) -> str:
    """Convert a pdfplumber table (list of rows) into readable text.
    Each row becomes: 'col1 | col2 | col3'
    """
    rows = []
    for row in table:
        cells = [str(c).strip() if c else "" for c in row]
        if any(cells):  # skip fully empty rows
            rows.append(" | ".join(cells))
    return "\n".join(rows)


# ── File Readers ──────────────────────────────────────────────

def read_pdf(path: str) -> str:
    """Extract text from PDF using pdfplumber with table detection.

    For each page:
    1. Detect tables → convert to readable text
    2. Extract remaining non-table text
    3. Combine both
    """
    all_text = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_parts = []

            # 1. Extract tables
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    page_parts.append(table_to_text(table))

            # 2. Extract regular text (pdfplumber handles layout better)
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                page_parts.append(text)

            if page_parts:
                all_text.append("\n\n".join(page_parts))

    raw = "\n\n".join(all_text)
    return clean_text(raw)


def read_csv(path: str) -> str:
    """Read CSV as clean text."""
    with open(path, "r", encoding="utf-8") as f:
        return clean_text(f.read())


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
        print(f"📄 Loading: {os.path.basename(pdf)}")
        text = read_pdf(pdf)
        print(f"   Cleaned: {len(text)} chars")
        # Show a sample of cleaned text
        print(f"   Sample:  {text[:150]}...")
        all_chunks.extend(chunk_text(text, os.path.basename(pdf)))

    for csv in glob.glob(str(DATA_DIR / "*.csv")):
        print(f"📊 Loading: {os.path.basename(csv)}")
        text = read_csv(csv)
        all_chunks.extend(chunk_text(text, os.path.basename(csv)))

    if not all_chunks:
        print("⚠️  No PDF/CSV files found in ingestion/data/")
        return

    print(f"✂️  {len(all_chunks)} chunks created")

    print("🔄 Embedding with Gemini...")
    for i, chunk in enumerate(all_chunks):
        chunk["vector"] = embed_text(chunk["text"])
        if (i + 1) % 10 == 0:
            print(f"   Embedded {i + 1}/{len(all_chunks)}")

    lance_db.create_table("documents", all_chunks, mode="overwrite")
    print(f"✅ Stored {len(all_chunks)} chunks in LanceDB")


if __name__ == "__main__":
    run()
