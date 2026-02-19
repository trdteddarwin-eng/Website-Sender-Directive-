#!/usr/bin/env python3
"""
Setup Email Monitor Infrastructure

Creates:
1. Google Sheet "Email Monitor - ted@tedca.com" with tracking columns
2. Gmail label "auto-processed" for ted@tedca.com

Run once to set up the infrastructure for the N8N workflow.
"""

import os
import json
import sys
from dotenv import load_dotenv
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

# Sheet columns
TRACKING_COLUMNS = [
    "email_id",
    "received_at",
    "processed_at",
    "sender_email",
    "sender_name",
    "subject",
    "body_preview",
    "category",
    "reply_sent",
    "reply_preview",
    "notification_sent",
    "error_message"
]

SHEET_NAME = "Email Monitor - ted@tedca.com"
GMAIL_LABEL = "auto-processed"


def get_sheets_credentials():
    """Get Google Sheets/Drive credentials from token.json."""
    if not os.path.exists('token.json'):
        print("Error: token.json not found")
        return None

    with open('token.json', 'r') as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"]
    )

    if creds.expired:
        creds.refresh(Request())
        # Save refreshed token
        with open('token.json', 'w') as f:
            json.dump({
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes),
                "universe_domain": "googleapis.com",
                "account": "",
                "expiry": creds.expiry.isoformat() + "Z" if creds.expiry else None
            }, f)

    return creds


def get_gmail_credentials():
    """Get Gmail credentials from gmail_token.json."""
    if not os.path.exists('gmail_token.json'):
        print("Error: gmail_token.json not found")
        return None

    with open('gmail_token.json', 'r') as f:
        token_data = json.load(f)

    # Add required scopes for labels and reading messages
    scopes = token_data.get("scopes", [])
    required_scopes = [
        "https://www.googleapis.com/auth/gmail.labels",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly"
    ]

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=scopes
    )

    if creds.expired:
        creds.refresh(Request())

    return creds


def create_tracking_sheet():
    """Create the Google Sheet for email tracking."""
    print(f"\n=== Creating Google Sheet: {SHEET_NAME} ===")

    creds = get_sheets_credentials()
    if not creds:
        return None

    client = gspread.authorize(creds)

    # Check if sheet already exists
    try:
        existing = client.open(SHEET_NAME)
        print(f"Sheet already exists: {existing.url}")
        return existing.url
    except gspread.SpreadsheetNotFound:
        pass

    # Create new sheet
    sheet = client.create(SHEET_NAME)
    print(f"Created sheet: {sheet.url}")

    # Add headers
    worksheet = sheet.sheet1
    worksheet.update(values=[TRACKING_COLUMNS], range_name='A1')
    print(f"Added {len(TRACKING_COLUMNS)} columns: {', '.join(TRACKING_COLUMNS)}")

    # Format header row (bold)
    worksheet.format('A1:L1', {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
    })

    # Freeze header row
    worksheet.freeze(rows=1)

    # Resize columns for readability
    sheet.batch_update({
        "requests": [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": len(TRACKING_COLUMNS)
                    },
                    "properties": {"pixelSize": 150},
                    "fields": "pixelSize"
                }
            }
        ]
    })

    print(f"Sheet configured successfully")
    return sheet.url


def create_gmail_label():
    """Create the Gmail label for marking processed emails."""
    print(f"\n=== Creating Gmail Label: {GMAIL_LABEL} ===")

    creds = get_gmail_credentials()
    if not creds:
        print("Skipping Gmail label creation (no credentials)")
        print("NOTE: You'll need to create the label manually in Gmail")
        return None

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Check if label already exists
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        for label in labels:
            if label['name'] == GMAIL_LABEL:
                print(f"Label already exists: {label['id']}")
                return label['id']

        # Create the label
        label_body = {
            'name': GMAIL_LABEL,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        created = service.users().labels().create(userId='me', body=label_body).execute()
        print(f"Created label: {created['id']}")
        return created['id']

    except Exception as e:
        print(f"Error creating label: {e}")
        print("You may need to create the label manually in Gmail")
        print(f"  1. Go to Gmail settings > Labels")
        print(f"  2. Create new label: '{GMAIL_LABEL}'")
        return None


def main():
    print("=" * 60)
    print("EMAIL MONITOR INFRASTRUCTURE SETUP")
    print("=" * 60)

    # Create tracking sheet
    sheet_url = create_tracking_sheet()

    # Create Gmail label
    label_id = create_gmail_label()

    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)

    if sheet_url:
        print(f"\nTracking Sheet: {sheet_url}")

    if label_id:
        print(f"Gmail Label ID: {label_id}")
    else:
        print(f"\nGmail Label: Create manually in Gmail settings")
        print(f"  Label name: '{GMAIL_LABEL}'")

    print("\nNext steps:")
    print("  1. Import the N8N workflow JSON")
    print("  2. Configure Gmail OAuth in N8N for ted@tedca.com")
    print("  3. Add Anthropic API key to N8N credentials")
    print("  4. Test with a manual trigger")


if __name__ == "__main__":
    main()
