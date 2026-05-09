"""
Gmail × Claude 邮件回复助手
用法：
  python main.py          — 交互式选邮件并生成回复草稿
  python main.py index    — 索引最近 100 封邮件到向量数据库
"""

import os
import sys
from dotenv import load_dotenv

from gmail_client import fetch_latest_emails, Email
from claude_client import generate_reply_draft
from vector_store import index_emails, search_similar, build_rag_prompt


def load_config() -> tuple[str, str]:
    load_dotenv()

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/client_secret.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")

    if not os.path.exists(credentials_path):
        print(f"错误：找不到 Gmail OAuth2 凭证文件：{credentials_path}")
        print("请参考 README 获取 client_secret.json 并放入 credentials/ 目录。")
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("错误：未设置 ANTHROPIC_API_KEY 环境变量。")
        print("请在 .env 文件中配置，或直接 export ANTHROPIC_API_KEY=...")
        sys.exit(1)

    return credentials_path, token_path


def display_email_list(emails: list[Email]) -> None:
    print("\n" + "=" * 60)
    print(f"{'#':>3}  {'发件人':<30}  {'主题'}")
    print("-" * 60)
    for i, mail in enumerate(emails, 1):
        sender_short = mail.sender[:28] if len(mail.sender) > 28 else mail.sender
        subject_short = mail.subject[:35] if len(mail.subject) > 35 else mail.subject
        print(f"{i:>3}. {sender_short:<30}  {subject_short}")
    print("=" * 60)


def pick_email(emails: list[Email]) -> Email:
    while True:
        try:
            choice = input(f"\n请选择邮件编号（1-{len(emails)}），或输入 q 退出：").strip()
            if choice.lower() == "q":
                print("已退出。")
                sys.exit(0)
            idx = int(choice) - 1
            if 0 <= idx < len(emails):
                return emails[idx]
            print(f"请输入 1 到 {len(emails)} 之间的数字。")
        except ValueError:
            print("输入无效，请输入数字。")


def show_email_detail(mail: Email) -> None:
    print("\n" + "─" * 60)
    print(f"发件人：{mail.sender}")
    print(f"日期：  {mail.date}")
    print(f"主题：  {mail.subject}")
    print("─" * 60)
    body_preview = (mail.body or mail.snippet)[:500]
    if len(mail.body or mail.snippet) > 500:
        body_preview += "…（正文已截断）"
    print(body_preview)
    print("─" * 60)


def cmd_index() -> None:
    """索引最近 100 封邮件到 ChromaDB 向量数据库。"""
    load_dotenv()

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/client_secret.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "credentials/token.json")

    if not os.path.exists(credentials_path):
        print(f"错误：找不到 Gmail OAuth2 凭证文件：{credentials_path}")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("错误：未设置 OPENAI_API_KEY，无法生成 embedding。")
        print("请在 .env 中配置 OPENAI_API_KEY 后重试。")
        sys.exit(1)

    print("正在连接 Gmail，获取最近 100 封邮件…")
    emails = fetch_latest_emails(credentials_path, token_path, count=100)

    if not emails:
        print("收件箱为空，无需索引。")
        return

    print(f"共获取 {len(emails)} 封邮件，正在向量化并写入数据库…")
    count = index_emails(emails)
    print(f"完成！已索引 {count} 封邮件。")


def main() -> None:
    credentials_path, token_path = load_config()

    print("正在连接 Gmail，获取最新邮件…")
    emails = fetch_latest_emails(credentials_path, token_path, count=10)

    if not emails:
        print("收件箱为空。")
        return

    display_email_list(emails)
    selected = pick_email(emails)
    show_email_detail(selected)

    extra = input("\n有额外要求吗？（直接回车跳过）：").strip()

    # RAG: 检索相似历史邮件（若未配置 OPENAI_API_KEY 则静默跳过）
    query = f"{selected.subject} {(selected.body or selected.snippet)[:200]}"
    similar = search_similar(query, n=5)

    if similar:
        print(f"\n[RAG] 找到 {len(similar)} 封相似历史邮件，已加入上下文。")

    user_message = build_rag_prompt(selected, similar, user_input=extra)
    draft = generate_reply_draft(user_message)

    print("\n" + "=" * 60)
    print("回复草稿已生成（以上）")
    print("=" * 60)

    save = input("\n是否将草稿保存到文件？(y/N)：").strip().lower()
    if save == "y":
        filename = f"draft_{selected.id[:8]}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"回复：{selected.subject}\n\n{draft}")
        print(f"草稿已保存到 {filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        cmd_index()
    else:
        main()
