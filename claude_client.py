import anthropic

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """你是一位专业的邮件助手，擅长撰写清晰、得体、符合语境的邮件回复。

请根据用户提供的原始邮件，生成一封合适的回复草稿。回复应：
- 语气与原邮件保持一致（正式/非正式）
- 直接切入主题，避免冗余
- 结构清晰，用词恰当
- 如有需要，可以保留占位符如 [你的名字] 供用户填写"""


def generate_reply_draft(user_message: str) -> str:
    """
    Stream a reply draft using Claude.
    `user_message` is a fully-assembled prompt (built by vector_store.build_rag_prompt
    or constructed manually). Returns the complete draft text.
    """
    client = anthropic.Anthropic()

    print("\n正在生成回复草稿", end="", flush=True)

    draft_parts: list[str] = []

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
                    text = delta.text
                    print(text, end="", flush=True)
                    draft_parts.append(text)
                elif delta.type == "thinking_delta":
                    print(".", end="", flush=True)

    print()  # newline after streaming
    return "".join(draft_parts)
