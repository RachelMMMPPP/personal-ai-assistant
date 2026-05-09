# Gmail × Claude Reply Assistant

An AI-powered email reply draft generator that connects Gmail with Claude. Supports RAG (Retrieval-Augmented Generation) using your own email history as context.

Available in two modes:
- **Web UI**: FastAPI backend + React frontend
- **CLI**: Interactive terminal mode

## Project Structure

```
gmail-claude-reply/
├── api.py             # FastAPI backend entry point
├── main.py            # CLI entry point
├── gmail_client.py    # Gmail API wrapper (OAuth2 + MIME parsing)
├── claude_client.py   # Claude API wrapper (streaming + adaptive thinking)
├── vector_store.py    # RAG layer (ChromaDB + OpenAI Embeddings)
├── requirements.txt
├── .env.example
├── frontend/          # React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── EmailList.tsx
│   │       ├── EmailDetail.tsx
│   │       └── DraftPanel.tsx
│   └── package.json
└── credentials/       # OAuth2 credentials (not committed to git)
```

## Setup

### 1. Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Get from [Anthropic Console](https://console.anthropic.com) |
| `OPENAI_API_KEY` | Optional — required for RAG embeddings; omit to disable RAG |
| `GMAIL_CREDENTIALS_PATH` | Path to OAuth2 credentials (default: `credentials/client_secret.json`) |
| `GMAIL_TOKEN_PATH` | Token cache path (default: `credentials/token.json`) |
| `CHROMA_DB_PATH` | Vector database path (default: `.chroma_db`) |

### 3. Gmail OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a project → enable the Gmail API
2. Create an OAuth 2.0 client ID (Desktop app type) and download the JSON file
3. Save it as `credentials/client_secret.json`
4. On first launch, a browser window will open for authorization; the token is then cached automatically

### 4. Frontend dependencies

```bash
cd frontend
npm install
```

## Running

### Web UI

Terminal 1 — start the backend:
```bash
uvicorn api:app --reload --port 8000
```

Terminal 2 — start the frontend:
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

### CLI

```bash
# Interactively generate a reply draft
python main.py

# Index the latest 100 emails into the vector database (enables RAG)
python main.py index
```

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/api/emails` | Fetch the 10 most recent inbox emails |
| POST | `/api/index` | Index the latest 100 emails into ChromaDB |
| POST | `/api/draft` | Generate a reply draft (SSE streaming) |

## RAG Architecture

```
User selects an email
        │
        ▼
search_similar(query, n=5)        ← ChromaDB cosine similarity search
        │
        ▼
build_rag_prompt(email, similar)  ← Assemble prompt with context + new email
        │
        ▼
Claude claude-opus-4-7            ← SSE streaming (adaptive thinking)
        │
        ▼
Frontend renders draft in real time
```

- **Vector database**: ChromaDB (local persistent storage, cosine similarity)
- **Embedding model**: OpenAI `text-embedding-3-small`
- **Graceful degradation**: If `OPENAI_API_KEY` is not set, RAG is silently skipped and drafts are generated without historical context

## Notes

- Gmail OAuth2 scope is read-only (`gmail.readonly`) — the app never modifies or sends emails
- The `.chroma_db/` directory holds the local vector store and is excluded from git
