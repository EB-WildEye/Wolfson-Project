# 🩺 Gali – Gynecology AI Assistant

A **stupid simple** RAG (Retrieval-Augmented Generation) system that lets you chat with an AI assistant grounded in your department's PDFs and CSVs.

Built for the Gynecology Department at **Wolfson Medical Center**.

---

## Architecture

```
Gali/
├── .python-version          # Python 3.12 (managed by uv)
├── pyproject.toml           # Dependencies (managed by uv)
├── .env                     # API keys
│
├── ingestion/               # Step 1: Ingest documents
│   ├── main.py              #   Load → Chunk → Embed → Store
│   └── data/                #   Drop your PDFs/CSVs here
│
├── agent/                   # Step 2: RAG logic
│   ├── main.py              #   Retrieve → Prompt → LLM → Answer
│   └── utils.py             #   Shared: ChromaDB connection, retriever
│
└── ui/                      # Step 3: Chat interface
    └── app.py               #   Streamlit chat UI
```

## Quick Start

### 1. Install dependencies

```bash
cd Gali/
uv sync
```

### 2. Set your API key

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Add documents

Drop your PDF and/or CSV files into `ingestion/data/`.

### 4. Ingest documents

```bash
uv run python -m ingestion.main
```

This will chunk your documents and store embeddings in a local ChromaDB at `./chroma_db/`.

### 5. Test the agent (CLI)

```bash
uv run python -m agent.main "What are the department guidelines for X?"
```

### 6. Launch the chat UI

```bash
uv run streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

---

## Tech Stack

| Component       | Technology           |
| --------------- | -------------------- |
| Language        | Python 3.12          |
| Package Manager | uv                   |
| LLM Framework   | LangChain            |
| LLM             | GPT-4o-mini (OpenAI) |
| Vector Store    | ChromaDB (local)     |
| Document Loaders| PyPDF, CSVLoader     |
| UI              | Streamlit            |

---

## ⚠️ Disclaimer

Gali is an AI assistant and does **NOT** replace professional medical advice.
Always consult a physician for medical decisions.
