# 🩺 Gali — Gynecology AI Assistant

> RAG-powered medical assistant for the Women's Health Department at **Wolfson Medical Center**.

Gali ingests department PDFs and CSVs, embeds them into a local vector store, and provides an AI chat interface grounded in real clinical documents — with built-in safety protocols, session history, and prompt-injection protection.

---

## Project Structure

```
Gali/
├── pyproject.toml                # Dependencies (managed by uv)
├── .python-version               # Python 3.12
├── .env                          # API keys & config (git-ignored)
│
├── ingestion/                    # Document ingestion pipeline
│   ├── main.py                   #   CLI: Load → Clean → Chunk → Embed → Store
│   └── data/                     #   Drop your PDFs / CSVs here
│
├── agent/                        # Backend — RAG engine + API
│   ├── server.py                 #   FastAPI REST API (routes, CORS, middleware)
│   ├── llm.py                    #   Gemini LLM client
│   ├── vectorstore.py            #   LanceDB vector store
│   ├── history.py                #   MongoDB chat history + summarization
│   ├── prompt.py                 #   System prompt & safety protocols
│   ├── config.py                 #   Centralized settings from .env
│   └── logger.py                 #   Structured logging
│
├── ui/                           # Frontend — Chat interface
│   └── app.py                    #   Streamlit chat UI
│
├── lancedb_data/                 # Vector DB storage (git-ignored)
└── logs/                         # Application logs
```

---

## Prerequisites

| Requirement                                    | Version |
| ---------------------------------------------- | ------- |
| [Python](https://www.python.org/)              | 3.12+   |
| [uv](https://docs.astral.sh/uv/)              | latest  |
| [MongoDB](https://www.mongodb.com/)            | 7.0+    |

---

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

Create a `.env` file with the following:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
EMBED_MODEL=gemini-embedding-001
MONGO_URI=mongodb://localhost:27017
LANCEDB_PATH=./lancedb_data
```

### 3. Add documents

Place your PDF and/or CSV files into `ingestion/data/`.

### 4. Ingest documents

```bash
uv run python -m ingestion.main
```

---

## CLI Reference

### Ingestion

| Command | Description |
| --- | --- |
| `uv run python -m ingestion.main` | **Incremental ingest** — processes only new or modified files (uses SHA-256 hash cache) |
| `uv run python -m ingestion.main --drop` | **Drop & re-ingest** — deletes the vector table, then re-ingests all files |
| `uv run python -m ingestion.main --purge` | **Full purge** — deletes the vector table AND the file hash cache, then re-ingests everything from scratch |
| `uv run python -m ingestion.main --drop-only` | **Drop only** — deletes the vector table and exits (no ingestion) |

> **When to use what:**
> - Added new files? → `uv run python -m ingestion.main` (incremental, skips unchanged files)
> - Changed existing files? → `uv run python -m ingestion.main` (detects changes via hash)
> - Want a clean slate? → `uv run python -m ingestion.main --purge`

### Services

| Command | Description |
| --- | --- |
| `sudo systemctl start mongod` | Start MongoDB |
| `mongosh --eval "db.runCommand({ ping: 1 })"` | Verify MongoDB is running |
| `uv run uvicorn agent.server:app --reload --port 8000` | Start the FastAPI backend |
| `uv run streamlit run ui/app.py` | Start the Streamlit chat UI |

---

## Running the Project

Start these **3 services in order**, each in its own terminal:

### Terminal 1 — 🍃 MongoDB

```bash
sudo systemctl start mongod
```

Verify:

```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```

### Terminal 2 — 🚀 Backend (FastAPI)

```bash
uv run uvicorn agent.server:app --reload --port 8000
```

### Terminal 3 — 🖥️ UI (Streamlit)

```bash
uv run streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Updating the Knowledge Base

When you add, modify, or remove documents:

1. Place new/updated files in `ingestion/data/`
2. Run the ingestion pipeline:

```bash
uv run python -m ingestion.main          # incremental (recommended)
uv run python -m ingestion.main --purge  # full rebuild
```

3. The backend picks up changes automatically — no restart needed.

---

## Tech Stack

| Component        | Technology                  |
| ---------------- | --------------------------- |
| Language         | Python 3.12                 |
| Package Manager  | uv                          |
| LLM              | Gemini 2.5 Flash (Google)   |
| Embeddings       | Gemini Embedding 001        |
| Vector Store     | LanceDB (local, serverless) |
| Chat History     | MongoDB                     |
| Backend          | FastAPI + Uvicorn            |
| UI               | Streamlit                   |
| Document Parsing | pdfplumber                  |
| Config           | pydantic-settings            |

---

## Running Tests

Make sure the backend is running first (Terminal 2 above), then:

**Windows (PowerShell / CMD):**
```bash
uv run pytest tests/test_rag.py -v
```

**WSL:**
```bash
pip install pytest requests && python -m pytest tests/test_rag.py -v
```

The tests send real questions to the API and verify the answers contain expected terms from the source PDFs. A passing test suite confirms the RAG system is working end-to-end.

---

## ⚠️ Disclaimer

Gali is an AI assistant and does **NOT** replace professional medical advice.
Always consult a physician for medical decisions.
