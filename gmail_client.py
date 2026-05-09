import os
import base64
import email as email_lib
from dataclasses import dataclass
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class Email:
    id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body: str


def authenticate(credentials_path: str, token_path: str) -> Credentials:
    """Run OAuth2 flow on first use; load cached token afterwards."""
    creds: Optional[Credentials] = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def _decode_body(payload: dict) -> str:
    """Recursively extract plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_latest_emails(credentials_path: str, token_path: str, count: int = 10) -> list[Email]:
    """Return the most recent `count` emails from the Gmail inbox."""
    creds = authenticate(credentials_path, token_path)
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me", maxResults=count, labelIds=["INBOX"]
    ).execute()

    messages = results.get("messages", [])
    emails: list[Email] = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full"
        ).execute()

        headers = msg["payload"].get("headers", [])
        body = _decode_body(msg["payload"])

        emails.append(Email(
            id=msg["id"],
            subject=_header(headers, "Subject") or "(no subject)",
            sender=_header(headers, "From"),
            date=_header(headers, "Date"),
            snippet=msg.get("snippet", ""),
            body=body,
        ))

    return emails
