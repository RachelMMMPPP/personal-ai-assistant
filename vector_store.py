"""
RAG 向量存储层
- 向量数据库：ChromaDB（本地持久化）
- Embedding 模型：OpenAI text-embedding-3-small
"""

import os
from typing import Any

import chromadb
from openai import OpenAI

from gmail_client import Email

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "gmail_emails"
# 每封邮件索引时保留的正文最大字符数（节省 embedding token）
_BODY_INDEX_LIMIT = 1500
# 组装 prompt 时每封参考邮件的摘要字符数
_BODY_SNIPPET_LIMIT = 350


def _chroma_path() -> str:
    return os.getenv("CHROMA_DB_PATH", ".chroma_db")


def _collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=_chroma_path())
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(texts: list[str]) -> list[list[float]]:
    """Call OpenAI Embeddings API and return a list of embedding vectors."""
    openai_client = OpenAI()
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def index_emails(emails: list[Email]) -> int:
    """
    向量化邮件列表并 upsert 到 ChromaDB。
    同一 email.id 重复调用时会覆盖旧向量（幂等）。
    返回实际索引的邮件数量。
    """
    if not emails:
        return 0

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "未设置 OPENAI_API_KEY，无法生成 embedding。"
            "请在 .env 中配置后重试。"
        )

    col = _collection()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for mail in emails:
        body = (mail.body or mail.snippet)[:_BODY_INDEX_LIMIT]
        document = f"{mail.subject}\n\n{body}"
        ids.append(mail.id)
        documents.append(document)
        metadatas.append({
            "subject": mail.subject,
            "sender": mail.sender,
            "date": mail.date,
        })

    # OpenAI API 单次请求最多 2048 条，分批处理以防大批量报错
    BATCH = 512
    all_embeddings: list[list[float]] = []
    for i in range(0, len(documents), BATCH):
        all_embeddings.extend(_embed(documents[i : i + BATCH]))

    col.upsert(
        ids=ids,
        documents=documents,
        embeddings=all_embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def search_similar(query: str, n: int = 5) -> list[dict[str, Any]]:
    """
    在向量库中检索与 query 最相似的 n 封邮件。
    若向量库为空或未配置 OPENAI_API_KEY，返回空列表（可降级为无 RAG 模式）。
    """
    if not os.getenv("OPENAI_API_KEY"):
        return []

    col = _collection()
    total = col.count()
    if total == 0:
        return []

    actual_n = min(n, total)
    query_embedding = _embed([query])[0]

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )

    similar: list[dict[str, Any]] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similar.append({
            "subject": meta["subject"],
            "sender": meta["sender"],
            "date": meta["date"],
            "body": doc,
            "distance": dist,  # cosine distance：越小越相似
        })
    return similar


def build_rag_prompt(
    new_email: Email,
    similar_emails: list[dict[str, Any]],
    user_input: str = "",
) -> str:
    """
    将「新邮件 + 相似历史邮件（RAG 上下文）+ 用户额外要求」
    组装成发给 Claude 的完整 user message。
    """
    # --- 历史邮件上下文块 ---
    context_block = ""
    if similar_emails:
        parts: list[str] = []
        for i, mail in enumerate(similar_emails, 1):
            # 只取正文前 N 字，避免 prompt 过长
            body_preview = mail["body"][:_BODY_SNIPPET_LIMIT]
            if len(mail["body"]) > _BODY_SNIPPET_LIMIT:
                body_preview += "…"
            parts.append(
                f"[参考邮件 {i} | 相似度 {1 - mail['distance']:.2f}]\n"
                f"发件人：{mail['sender']}\n"
                f"日期：{mail['date']}\n"
                f"主题：{mail['subject']}\n"
                f"内容节选：{body_preview}"
            )
        context_block = (
            "以下是历史上收到的相似邮件，仅供语气和处理方式参考：\n\n"
            + "\n\n".join(parts)
            + "\n\n" + "─" * 40 + "\n\n"
        )

    # --- 待回复邮件 ---
    new_body = (new_email.body or new_email.snippet).strip()
    prompt = (
        f"{context_block}"
        f"请为以下邮件生成一封回复草稿：\n\n"
        f"发件人：{new_email.sender}\n"
        f"日期：{new_email.date}\n"
        f"主题：{new_email.subject}\n\n"
        f"正文：\n{new_body}"
    )

    if user_input:
        prompt += f"\n\n额外要求：{user_input}"

    return prompt
