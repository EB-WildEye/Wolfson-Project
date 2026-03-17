# 🩺 Gali — Gynecology AI Assistant

> RAG-powered medical assistant for the Women's Health Department at **Wolfson Medical Center**.

Gali ingests department PDFs and CSVs, embeds them into **LanceDB** (vector store), and provides an AI chat interface grounded in real clinical documents — with built-in safety protocols, ephemeral session history (**MongoDB**), and prompt-injection protection.

---

## Project Structure

```
Gali/
├── shared/                       # Shared Lambda Layer
│   ├── db.py                     #   MongoDB session store (chat history ONLY — not RAG)
│   ├── pii.py                    #   PII scrubbing (IDs, phones, emails)
│   └── config.py                 #   Secrets Manager + env settings
│
├── endpoints/                    # API Lambdas
│   ├── session/                  #   λ1 — Session: UUID + history retrieval
│   ├── chat/                     #   λ2 — Chat: RAG pipeline (LanceDB + Gemini)
│   └── cleanup/                  #   λ4 — Cleanup: delete messages > 24h
│
├── data/                         # Ingestion Lambda
│   └── handler.py                #   λ3 — S3 trigger → embed → store in LanceDB
│
├── frontend/                     # Next.js App (AWS Amplify)
│   └── src/
│
├── agent/                        # OLD MONOLITH (kept for reference)
├── ingestion/                    # OLD INGESTION (kept for reference)
├── lancedb_data/                 # Vector DB storage (git-ignored)
└── .env                          # API keys & config (git-ignored)
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

## Data Store Roles

| Store | Purpose | Data Lifetime | Used By |
|-------|---------|---------------|---------|
| **LanceDB** | Vector Store — RAG knowledge base (embedded medical protocols) | Permanent | λ2 Chat, λ3 Ingestion |
| **MongoDB** | Session Store — ephemeral chat messages (user ↔ assistant turns) | **24 hours** (then deleted) | λ1 Session, λ2 Chat, λ4 Cleanup |

> **Crucial:** No vector search or RAG is performed on MongoDB. All RAG retrieval goes through LanceDB.

## Tech Stack

| Component        | Technology                         |
| ---------------- | ---------------------------------- |
| Language         | Python 3.12                        |
| LLM              | Gemini 2.5 Flash (Google)          |
| Embeddings       | Gemini Embedding 001               |
| Vector Store     | LanceDB (RAG knowledge retrieval)  |
| Session Store    | MongoDB (ephemeral chat history)   |
| Backend          | AWS Lambda + Powertools            |
| API              | API Gateway (HTTP)                 |
| Frontend         | Next.js 14 (React) — AWS Amplify   |
| Document Parsing | pdfplumber                         |
| Config           | AWS Secrets Manager + env vars     |

---

## ⚠️ Disclaimer

Gali is an AI assistant and does **NOT** replace professional medical advice.
Always consult a physician for medical decisions.
