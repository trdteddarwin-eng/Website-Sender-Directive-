"""Gmail send/draft wrapper — sends drafts and creates new ones."""

import os
import sys
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GMAIL_TOKEN_PATH, GMAIL_CREDS_PATH

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def _get_gmail_service():
    """Authenticate and return Gmail API service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(GMAIL_TOKEN_PATH):
        try:
            with open(GMAIL_TOKEN_PATH, "r") as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GMAIL_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(GMAIL_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_draft(draft_id):
    """Send an existing Gmail draft by its ID.

    Returns dict with message_id, thread_id on success.
    """
    service = _get_gmail_service()
    result = service.users().drafts().send(
        userId="me",
        body={"id": draft_id}
    ).execute()
    return {
        "message_id": result.get("id", ""),
        "thread_id": result.get("threadId", ""),
    }


def get_thread_messages(thread_id):
    """Get all messages in a Gmail thread.

    Returns list of dicts with id, from, subject, snippet, date.
    """
    service = _get_gmail_service()
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="metadata",
        metadataHeaders=["From", "Subject", "Date"]
    ).execute()

    messages = []
    for msg in thread.get("messages", []):
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        messages.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "snippet": msg.get("snippet", ""),
            "date": headers.get("Date", ""),
            "label_ids": msg.get("labelIds", []),
        })
    return messages


def get_message_body(message_id):
    """Get the full body text of a message."""
    service = _get_gmail_service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    def _extract_text(payload):
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            text = _extract_text(part)
            if text:
                return text
        return ""

    return _extract_text(msg.get("payload", {}))


def check_gmail_auth():
    """Test Gmail OAuth connection. Returns True if authenticated."""
    try:
        service = _get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        return {"ok": True, "email": profile.get("emailAddress", "")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_sent_emails_with_threads(limit=100):
    """Get recently sent emails with their thread IDs for reply checking."""
    service = _get_gmail_service()
    results = service.users().messages().list(
        userId="me", labelIds=["SENT"], maxResults=limit
    ).execute()

    messages = []
    for msg_ref in results.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["To", "Subject"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        messages.append({
            "id": msg["id"],
            "thread_id": msg.get("threadId", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
        })
    return messages
