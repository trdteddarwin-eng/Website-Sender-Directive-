#!/usr/bin/env python3
"""
Create a Gmail draft with HTML body and inline image attachments.

Usage:
    python3 execution/create_gmail_draft.py \
        --to "owner@example-hvac.com" \
        --subject "Your new website" \
        --html_file .tmp/acme-hvac/outreach-email.html \
        --attach .tmp/acme-hvac/old-site.png:old-site-screenshot \
        --attach .tmp/acme-hvac/new-site.png:new-site-screenshot

    # Or with inline HTML:
    python3 execution/create_gmail_draft.py \
        --to "owner@example.com" \
        --subject "Test" \
        --html "<h1>Hello</h1>"

Attachments use format: filepath:content-id
The content-id maps to <img src="cid:content-id"> in the HTML.
"""

import os
import sys
import json
import re
import argparse
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]

# Look for gmail-specific token first, fall back to general token
GMAIL_TOKEN_PATH = "gmail_token.json"
GMAIL_CREDS_PATH = "gmail_credentials.json"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH):
        try:
            with open(GMAIL_TOKEN_PATH, "r") as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}", file=sys.stderr)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
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


def validate_email(email):
    """Basic email validation. Returns True if email looks valid."""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def create_draft(to_email, subject, html_body, attachments=None, from_name="Ted"):
    """
    Create a Gmail draft with HTML body and optional inline image attachments.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML content of the email
        attachments: List of (file_path, content_id) tuples for inline images
        from_name: Display name for the From field

    Returns:
        dict with draft_id and message_id
    """
    # Validate email before proceeding
    if not validate_email(to_email):
        print(f"Error: Invalid email address: '{to_email}'", file=sys.stderr)
        return None

    service = get_gmail_service()

    # Get sender's email
    profile = service.users().getProfile(userId="me").execute()
    sender_email = profile["emailAddress"]

    # Build the MIME message
    msg = MIMEMultipart("related")
    msg["To"] = to_email
    msg["From"] = f"{from_name} <{sender_email}>"
    msg["Subject"] = subject

    # Attach HTML body
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    # Attach inline images
    if attachments:
        for file_path, content_id in attachments:
            if not os.path.exists(file_path):
                print(f"Warning: Attachment not found: {file_path}", file=sys.stderr)
                continue

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith("image/"):
                subtype = mime_type.split("/")[1]
                with open(file_path, "rb") as f:
                    img_data = f.read()
                img_part = MIMEImage(img_data, _subtype=subtype)
                img_part.add_header("Content-ID", f"<{content_id}>")
                img_part.add_header("Content-Disposition", "inline", filename=os.path.basename(file_path))
                msg.attach(img_part)
                print(f"  Attached: {file_path} as cid:{content_id}")
            else:
                # Non-image attachment
                with open(file_path, "rb") as f:
                    file_data = f.read()
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
                msg.attach(part)
                print(f"  Attached: {file_path}")

    # Encode and create draft
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw_message}}
    ).execute()

    draft_id = draft["id"]
    message_id = draft.get("message", {}).get("id", "")

    print(f"Draft created successfully!")
    print(f"  Draft ID: {draft_id}")
    print(f"  To: {to_email}")
    print(f"  Subject: {subject}")

    return {"draft_id": draft_id, "message_id": message_id}


def main():
    parser = argparse.ArgumentParser(description="Create a Gmail draft with HTML body and inline images")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--html_file", help="Path to HTML file for email body")
    parser.add_argument("--html", help="Inline HTML string for email body")
    parser.add_argument("--attach", action="append", help="Inline image: filepath:content-id (repeatable)")
    parser.add_argument("--from_name", default="Ted", help="Display name for From field (default: Ted)")
    parser.add_argument("--output", help="Save draft info to JSON file")

    args = parser.parse_args()

    # Get HTML body
    if args.html_file:
        with open(args.html_file, "r") as f:
            html_body = f.read()
    elif args.html:
        html_body = args.html
    else:
        parser.error("Must provide either --html_file or --html")
        return

    # Parse attachments
    attachments = []
    if args.attach:
        for att in args.attach:
            if ":" not in att:
                print(f"Warning: Invalid attachment format '{att}'. Use filepath:content-id", file=sys.stderr)
                continue
            file_path, content_id = att.rsplit(":", 1)
            attachments.append((file_path, content_id))

    # Create the draft
    result = create_draft(
        to_email=args.to,
        subject=args.subject,
        html_body=html_body,
        attachments=attachments if attachments else None,
        from_name=args.from_name,
    )

    # Optionally save result
    if args.output and result:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Draft info saved to: {args.output}")

    return result


if __name__ == "__main__":
    main()
