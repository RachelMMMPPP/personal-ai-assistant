"""
FastAPI backend for Gmail × Claude 邮件回复助手

启动方式：uvicorn api:app --reload --port 8000
"""

import json
import os

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

from gmail_client import Email, fetch_latest_emails
from vector_store import build_rag_prompt, index_emails, search_similar

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """你是一位专业的邮件助手，擅长撰写清晰、得体、符合语境的邮件回复。

请根据用户提供的原始邮件，生成一封合适的回复草稿。回复应：
- 语气与原邮件保持一致（正式/非正式）
- 直接切入主题，避免冗余
- 结构清晰，用词恰当
- 如有需要，可以保留占位符如 [你的名字] 供用户填写"""

app = FastAPI(title="Gmail Claude Reply API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _credentials() -> tuple[str, str]:
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/client_secret.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")
    return credentials_path, token_path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/emails")
def list_emails():
    credentials_path, token_path = _credentials()
    try:
        emails = fetch_latest_emails(credentials_path, token_path, count=10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return [
        {
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "date": e.date,
            "snippet": e.snippet,
            "body": e.body,
        }
        for e in emails
    ]


@app.post("/api/index")
def index_email_store():
    credentials_path, token_path = _credentials()
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY 未设置，无法生成 embedding。")
    try:
        emails = fetch_latest_emails(credentials_path, token_path, count=100)
        count = index_emails(emails)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"indexed": count}


class DraftRequest(BaseModel):
    email_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str
    extra: str = ""


@app.post("/api/draft")
def generate_draft(req: DraftRequest):
    email = Email(
        id=req.email_id,
        subject=req.subject,
        sender=req.sender,
        date=req.date,
        snippet=req.snippet,
        body=req.body,
    )

    query = f"{req.subject} {(req.body or req.snippet)[:200]}"
    similar = search_similar(query, n=5)
    user_message = build_rag_prompt(email, similar, user_input=req.extra)
    rag_count = len(similar)

    def event_stream():
        yield f"data: {json.dumps({'type': 'rag', 'count': rag_count})}\n\n"
        try:
            client = anthropic.Anthropic()
            with client.messages.stream(
                model=MODEL,
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield f"data: {json.dumps({'type': 'text', 'text': delta.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
