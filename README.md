# 🩺 Gali – Gynecology AI Assistant

A **stupid simple** RAG (Retrieval-Augmented Generation) system that lets you chat with an AI assistant grounded in your department's PDFs and CSVs.

Built for the Gynecology Department at **Wolfson Medical Center**.

---

## Architecture

```
Gali/
├── .python-version          # Python 3.12 (managed by uv)
├── pyproject.toml           # Dependencies (managed by uv)
├── .env                     # API keys & config
│
├── ingestion/               # Step 1: Ingest documents
│   ├── main.py              #   Load → Chunk → Embed → Store
│   └── data/                #   Drop your PDFs/CSVs here
│
├── agent/                   # Step 2: RAG logic + API server
│   ├── server.py            #   FastAPI REST API
│   ├── llm.py               #   Gemini LLM client
│   ├── vectorstore.py       #   LanceDB vector store
│   ├── history.py           #   MongoDB chat history
│   ├── prompt.py            #   Prompt templates
│   ├── config.py            #   Settings from .env
│   └── logger.py            #   Logging setup
│
└── ui/                      # Step 3: Chat interface
    └── app.py               #   Streamlit chat UI
```

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **MongoDB 7.0+** — for chat history storage

---

## Quick Start

### 1. Install dependencies

```bash
cd Gali/
uv sync
```

### 2. Configure environment

Edit `.env` and set your Gemini API key:

```
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-2.5-pro
EMBED_MODEL=gemini-embedding-001
MONGO_URI=mongodb://localhost:27017
LANCEDB_PATH=./lancedb_data
```

### 3. Add documents

Drop your PDF and/or CSV files into `ingestion/data/`.

### 4. Ingest documents

```bash
uv run python -m ingestion.main
```

This will chunk your documents and store embeddings in a local LanceDB at `./lancedb_data/`.

---

## Running the Project

You need **3 terminals** (all from the `Gali/` directory). Start them in this order:

### Terminal 1 — 🍃 MongoDB

```bash
sudo systemctl start mongod
```

Verify it's running:

```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```

### Terminal 2 — 🚀 Backend (FastAPI)

```bash
uv run uvicorn agent.server:app --reload --port 8000
```

API will be available at http://localhost:8000 (docs at http://localhost:8000/docs).

### Terminal 3 — 🖥️ UI (Streamlit)

```bash
uv run streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

---

## Tech Stack

| Component        | Technology                    |
| ---------------- | ----------------------------- |
| Language         | Python 3.12                   |
| Package Manager  | uv                            |
| LLM              | Gemini 2.5 Pro (Google)       |
| Embeddings       | Gemini Embedding 001          |
| Vector Store     | LanceDB (local, serverless)   |
| Chat History     | MongoDB                       |
| Backend API      | FastAPI + Uvicorn              |
| UI               | Streamlit                     |
| Document Loaders | pdfplumber                    |

---

## API Endpoints

| Method | Endpoint                        | Description              |
| ------ | ------------------------------- | ------------------------ |
| POST   | `/api/v1/chat`                  | Send a chat message      |
| GET    | `/api/v1/history/{session_id}`  | Get session chat history |
| GET    | `/api/v1/health`                | Health check             |

---

## ⚠️ Disclaimer

Gali is an AI assistant and does **NOT** replace professional medical advice.
Always consult a physician for medical decisions.
