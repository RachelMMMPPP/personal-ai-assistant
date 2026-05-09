# Personal AI Assistant — Auto-Reply in My Own Voice

## Project Overview

This project builds a personal AI assistant that reads my emails and generates reply drafts that sound like **me** — matching my personal tone and writing style.

The original goal was to automate both Gmail and WhatsApp replies. I collected personal messaging data from both platforms for model training, but ran into a key limitation with WhatsApp — automating replies on a personal account is not officially supported. Using the WhatsApp API requires a **WhatsApp Business Account** with Meta verification, which is inaccessible for personal projects. The current demo therefore focuses on Gmail.

---

## Two Approaches

### Approach 1: Using Existing LLM API (Current Project)
Directly integrates **Claude API** with Prompt Engineering to mimic my writing style, combined with Gmail API to read emails and save reply drafts.

### Approach 2: Training My Own Model (Research Version)
Collected personal messaging data, fine-tuned multiple open-source models, and deployed the best-performing model to generate personalized replies.

---

## Approach 2 — Detailed Process

### Step 1: Data Collection

**Gmail Data**
- Exported personal email history using Gmail API
- Extracted sender, recipient, subject, and body, formatted into training pairs

**WhatsApp Data**
- Manually exported chat history from phone (.txt format)
- Parsed using a Python script to extract conversation pairs (input → my reply)
- After data augmentation: ~5,000 → ~7,700 samples

**Why WhatsApp data?**

WhatsApp conversations better reflect my natural, everyday tone compared to formal emails. Combining both sources gives the model a more complete picture of how I communicate.

---

### Step 2: Model Training & Comparison

Fine-tuned 4 open-source models using **LoRA** on Google Colab, with each training run taking several hours:

| Model | Parameters |
|---|---|
| Gemma-2B | 2B |
| Phi-4 | 14B |
| Llama 3.1 | 8B |
| Qwen-2.5 | 7B |

Two rounds of experiments were conducted:
- **Demo 1**: ~5,000 original samples
- **Demo 2**: ~7,700 samples after data augmentation — overall performance improved

---

### Step 3: Model Evaluation

#### Metric Comparison vs GPT Baseline

**Demo 1 (~5,000 samples)**

| Metric | GPT Baseline | Llama3.1-8B | Phi4 | Gemma-2B | Qwen-2.5 |
|---|---|---|---|---|---|
| Toxicity | 0.0005 | 0.0058 | 0.0024 | 0.0021 | 0.0014 |
| Cosine Similarity | 0.8049 | 0.8199 | 0.8562 | 0.8191 | 0.7995 |
| Context Relevance | 0.713 | 0.796 | 0.7633 | 0.86 | 0.6595 |
| Style Similarity | 0.666 | 0.738 | 0.7769 | 0.812 | 0.6595 |

**Demo 2 (~7,700 samples, after data augmentation)**

| Metric | GPT Baseline | Llama3.1-8B | Phi4 | Gemma-2B | Qwen-2.5 |
|---|---|---|---|---|---|
| Toxicity | 0.0013 | 0.0015 | 0.0022 | 0.0013 | 0.0023 |
| Cosine Similarity | 0.8376 | 0.8229 | 0.7959 | 0.8455 | 0.8047 |
| Context Relevance | 0.735 | 0.819 | 0.8168 | 0.854 | 0.6705 |
| Style Similarity | 0.6926 | 0.7107 | 0.7939 | 0.804 | 0.6137 |

**Key Findings:**
- Data augmentation improved overall performance across models
- **Gemma-2B achieved the best results**, outperforming the GPT Baseline in both Style Similarity and Context Relevance
- Qwen-2.5 performed the worst among the four models

---

#### MMLU General Knowledge Test

Performance on MMLU benchmark (57 domains covering STEM, Humanities, etc.) before and after fine-tuning:

| Model | Original Score | Fine-Tuned Score |
|---|---|---|
| Phi4 | 84.8 | 73.4 |
| Llama3.1-8B | 66.7 | 57.6 |
| Qwen-2.5 | 65.6 | 58.0 |
| Gemma-2B | 51.3 | 32.6 |

**Observation:** All models show a consistent drop in general knowledge after fine-tuning. This is a known trade-off — as models specialize in a specific style, they lose some broad general capability. This highlights the **tension between personalization and general intelligence**.

---

### Step 4: Model Deployment

**GCP Compute Engine**
- Launched a GPU VM instance, uploaded fine-tuned model weights
- Pros: Stable, fully customizable
- Cons: Requires manual server management, higher cost

**RunPod (also tested)**
- On-demand GPU rental, simpler and faster to set up
- Pros: Cost-effective, flexible for testing
- Cons: Less stable compared to GCP

---

## Why No WhatsApp Auto-Reply?

Using the WhatsApp API requires:
- A verified **WhatsApp Business Account**
- A dedicated phone number registered to the Business API
- Approval from Meta Business Manager

This makes it inaccessible for personal automation projects, so the current version demonstrates Gmail only.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | Python + FastAPI |
| Email Integration | Gmail API |
| AI Model (Approach 1) | Claude API |
| AI Model (Approach 2) | Gemma-2B / Phi4 / Llama3.1 / Qwen-2.5 |
| Fine-Tuning Method | LoRA |
| Training Platform | Google Colab |
| Model Deployment | GCP Compute Engine / RunPod |
| Vector Database | ChromaDB |

---

## System Architecture

```
Frontend (React)
    ↓ sends request
Backend (FastAPI)
    ↓ fetch emails          ↓ call model
Gmail API          Claude API / Self-deployed Model
    ↓ return emails         ↓ generate draft
        └──→ save draft to Gmail Drafts
```


# Approach 1: Gmail × Claude Reply Assistant

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
