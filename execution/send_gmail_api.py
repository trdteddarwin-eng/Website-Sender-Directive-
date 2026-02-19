#!/usr/bin/env python3
"""
Gmail API Email Sending Engine

Reads leads from a Google Sheet, renders personalized email templates,
and sends via Gmail API with OAuth authentication.

Alternative to SMTP-based send_cold_emails.py - uses Gmail API directly.
"""

import os
import sys
import json
import argparse
import time
import random
import hashlib
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Tracking columns added to the sheet
TRACKING_COLUMNS = [
    "send_status",       # sent, failed, bounced, pending
    "send_timestamp",    # ISO timestamp of last send
    "sending_account",   # which email account sent it
    "send_step",         # which step in the sequence (1, 2, 3)
    "send_message_id",   # Gmail message ID for tracking
    "send_error",        # error message if failed
]


def get_credentials():
    """Get Google OAuth credentials with Gmail API scope."""
    creds = None
    if os.path.exists('token.json'):
        try:
            with open('token.json', 'r') as token:
                token_data = json.load(token)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def extract_sheet_id(url):
    """Extract Google Sheet ID from URL."""
    if '/d/' in url:
        return url.split('/d/')[1].split('/')[0]
    return url


def column_letter(n):
    """Convert 0-based column index to Excel-style letter (A, B, ... Z, AA, AB, ...)."""
    result = ""
    while n >= 0:
        result = chr(65 + (n % 26)) + result
        n = n // 26 - 1
    return result


def load_template(template_name, step):
    """
    Load an email template file.
    Looks in execution/email_templates/{template_name}/step_{step}.txt
    Returns dict with 'subject' (first line) and 'body' (rest).
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "email_templates")
    # Try .txt first (plain text preferred for cold email), then .html
    for ext in [".txt", ".html"]:
        path = os.path.join(templates_dir, template_name, f"step_{step}{ext}")
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read().strip()
            lines = content.split('\n', 1)
            subject = lines[0].replace("Subject: ", "").strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            return {"subject": subject, "body": body, "path": path}

    print(f"Error: Template not found: {template_name}/step_{step}")
    return None


def render_template(template, lead):
    """
    Replace personalization variables in template subject and body.
    Variables: {first_name}, {company}, {city}, {icebreaker}, {roi_icebreaker},
               {casual_first_name}, {casual_company_name}, {casual_city_name}
    """
    subject = template["subject"]
    body = template["body"]

    variables = {
        "first_name": lead.get("first_name", ""),
        "company": lead.get("company_name", ""),
        "city": lead.get("city", ""),
        "icebreaker": lead.get("icebreaker", ""),
        "roi_icebreaker": lead.get("roi_icebreaker", ""),
        "casual_first_name": lead.get("casual_first_name", lead.get("first_name", "")),
        "casual_company_name": lead.get("casual_company_name", lead.get("company_name", "")),
        "casual_city_name": lead.get("casual_city_name", lead.get("city", "")),
        "email": lead.get("email", ""),
        "website": lead.get("website", lead.get("company_domain", "")),
    }

    for key, value in variables.items():
        placeholder = "{" + key + "}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))

    return {"subject": subject, "body": body}


def generate_message_id(from_email, to_email, step):
    """Generate a unique message ID for tracking."""
    unique = f"{from_email}-{to_email}-{step}-{time.time()}"
    hash_part = hashlib.md5(unique.encode()).hexdigest()[:12]
    domain = from_email.split("@")[1]
    return f"<{hash_part}.{step}@{domain}>"


def send_email_gmail_api(service, from_email, to_email, subject, body, message_id, dry_run=False):
    """
    Send a single email via Gmail API.
    Returns dict with status and details.
    """
    if dry_run:
        print(f"  [DRY RUN] Would send to {to_email} from {from_email}")
        print(f"    Subject: {subject}")
        print(f"    Body preview: {body[:100]}...")
        return {"status": "dry_run", "message_id": message_id}

    try:
        # Build the message
        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Message-ID"] = message_id

        # Plain text body (preferred for cold email - better deliverability)
        msg.attach(MIMEText(body, "plain"))

        # Encode message for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

        # Send via Gmail API
        # Use 'me' for authenticated user, or specific email if delegated access
        send_result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        gmail_message_id = send_result.get('id', message_id)
        return {"status": "sent", "message_id": gmail_message_id}

    except Exception as e:
        error_str = str(e)
        # Check for bounce-like errors
        if 'invalid' in error_str.lower() or 'recipient' in error_str.lower():
            return {"status": "bounced", "error": error_str, "message_id": message_id}
        return {"status": "failed", "error": error_str, "message_id": message_id}


def ensure_tracking_columns(worksheet, headers):
    """Add tracking columns to the sheet if they don't exist."""
    columns_to_create = []
    col_indices = {}

    for col_name in TRACKING_COLUMNS:
        if col_name in headers:
            col_indices[col_name] = headers.index(col_name)
        else:
            columns_to_create.append(col_name)
            idx = len(headers)
            col_indices[col_name] = idx
            headers.append(col_name)

    if columns_to_create:
        print(f"Creating {len(columns_to_create)} tracking columns: {', '.join(columns_to_create)}")
        current_cols = worksheet.col_count
        needed_cols = len(headers)
        if needed_cols > current_cols:
            worksheet.resize(cols=needed_cols)

        header_updates = [
            {'range': f'{column_letter(col_indices[col])}1', 'values': [[col]]}
            for col in columns_to_create
        ]
        if header_updates:
            worksheet.batch_update(header_updates)

    return col_indices


def update_send_status(worksheet, row_num, col_indices, status, account_email, step, message_id, error=""):
    """Write send tracking data back to the sheet for a single row."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = [
        {'range': f'{column_letter(col_indices["send_status"])}{row_num}', 'values': [[status]]},
        {'range': f'{column_letter(col_indices["send_timestamp"])}{row_num}', 'values': [[now]]},
        {'range': f'{column_letter(col_indices["sending_account"])}{row_num}', 'values': [[account_email]]},
        {'range': f'{column_letter(col_indices["send_step"])}{row_num}', 'values': [[str(step)]]},
        {'range': f'{column_letter(col_indices["send_message_id"])}{row_num}', 'values': [[message_id]]},
        {'range': f'{column_letter(col_indices["send_error"])}{row_num}', 'values': [[error]]},
    ]
    try:
        worksheet.batch_update(updates)
    except Exception as e:
        print(f"  Warning: Failed to update tracking for row {row_num}: {e}")


def get_leads_to_send(rows, headers, step, col_indices, follow_up_days=None):
    """
    Determine which leads to send to based on step and current status.

    Step 1: Send to leads with no send_status or send_status == 'pending'
    Step 2+: Send to leads where send_step == (step-1) and enough days have passed
    """
    email_idx = headers.index("email") if "email" in headers else None
    if email_idx is None:
        print("Error: No 'email' column found")
        return []

    status_idx = col_indices.get("send_status")
    step_idx = col_indices.get("send_step")
    ts_idx = col_indices.get("send_timestamp")

    leads = []
    for i, row in enumerate(rows[1:], start=2):  # row_num is 1-indexed, skip header
        if len(row) <= email_idx:
            continue
        email = row[email_idx].strip()
        if not email or "@" not in email:
            continue

        current_status = row[status_idx].strip() if status_idx is not None and len(row) > status_idx else ""
        current_step = row[step_idx].strip() if step_idx is not None and len(row) > step_idx else ""
        send_ts = row[ts_idx].strip() if ts_idx is not None and len(row) > ts_idx else ""

        # Skip bounced leads
        if current_status == "bounced":
            continue

        if step == 1:
            # Step 1: send to leads not yet sent
            if current_status in ("", "pending"):
                lead = build_lead_dict(row, headers, i)
                leads.append(lead)
        else:
            # Follow-up steps: check if previous step was sent and enough time passed
            if current_status != "sent":
                continue
            if current_step != str(step - 1):
                continue

            # Check if enough days have passed since last send
            if follow_up_days and send_ts:
                try:
                    last_sent = datetime.strptime(send_ts[:19], "%Y-%m-%d %H:%M:%S")
                    days_elapsed = (datetime.now() - last_sent).days
                    if days_elapsed < follow_up_days:
                        continue
                except ValueError:
                    pass

            lead = build_lead_dict(row, headers, i)
            leads.append(lead)

    return leads


def build_lead_dict(row, headers, row_num):
    """Build a lead dictionary from a row."""
    lead = {"_row_num": row_num}
    for j, header in enumerate(headers):
        if j < len(row):
            lead[header] = row[j].strip()
        else:
            lead[header] = ""
    return lead


def count_todays_sends(rows, headers, from_email):
    """Count how many emails were sent today from the specified account."""
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0

    if "send_timestamp" not in headers or "sending_account" not in headers:
        return 0

    ts_idx = headers.index("send_timestamp")
    acct_idx = headers.index("sending_account")
    status_idx = headers.index("send_status") if "send_status" in headers else None

    for row in rows[1:]:  # Skip header
        if len(row) <= max(ts_idx, acct_idx):
            continue

        timestamp = row[ts_idx].strip() if len(row) > ts_idx else ""
        account = row[acct_idx].strip() if len(row) > acct_idx else ""
        status = row[status_idx].strip() if status_idx and len(row) > status_idx else ""

        if not timestamp or not account:
            continue

        # Check if this send was today and from this account
        if timestamp.startswith(today) and account == from_email and status in ("sent", "dry_run"):
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Gmail API email sending engine with OAuth and tracking"
    )
    parser.add_argument("--sheet_url", required=True, help="Google Sheet URL with leads")
    parser.add_argument("--template_name", required=True, help="Template folder name (e.g., free_ai_audit)")
    parser.add_argument("--step", type=int, default=1, help="Sequence step to send (1=initial, 2=follow-up, etc.)")
    parser.add_argument("--max_sends", type=int, default=None,
                        help="Max emails to send in this run")
    parser.add_argument("--delay_range", default="60-180",
                        help="Random delay range in seconds between sends (e.g., 60-180)")
    parser.add_argument("--follow_up_days", type=int, default=3,
                        help="Days to wait before sending follow-up (default: 3)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Preview sends without actually sending")
    parser.add_argument("--from_email", default=None,
                        help="Gmail account to send from (default: authenticated user's primary email)")
    parser.add_argument("--worksheet", default=None, help="Worksheet name (default: first sheet)")

    args = parser.parse_args()

    # Parse delay range
    try:
        delay_parts = args.delay_range.split("-")
        delay_min = int(delay_parts[0])
        delay_max = int(delay_parts[1]) if len(delay_parts) > 1 else delay_min
    except (ValueError, IndexError):
        print(f"Error: Invalid delay range '{args.delay_range}'. Use format: MIN-MAX (e.g., 60-180)")
        sys.exit(1)

    # Load template
    template = load_template(args.template_name, args.step)
    if not template:
        sys.exit(1)
    print(f"Loaded template: {template['path']}")
    print(f"  Subject: {template['subject']}")

    # Get credentials and build services
    print(f"\nAuthenticating with Google...")
    creds = get_credentials()

    # Build Gmail service
    gmail_service = build('gmail', 'v1', credentials=creds)

    # Get the authenticated user's email if not specified
    from_email = args.from_email
    if not from_email:
        profile = gmail_service.users().getProfile(userId='me').execute()
        from_email = profile['emailAddress']

    print(f"Sending from: {from_email}")

    # Connect to Google Sheet
    print(f"\nConnecting to Google Sheet...")
    client = gspread.authorize(creds)
    sheet_id = extract_sheet_id(args.sheet_url)
    spreadsheet = client.open_by_key(sheet_id)

    if args.worksheet:
        worksheet = spreadsheet.worksheet(args.worksheet)
    else:
        worksheet = spreadsheet.sheet1

    # Read all data
    rows = worksheet.get_all_values()
    if not rows:
        print("Sheet is empty")
        sys.exit(0)

    headers = rows[0]

    # Ensure tracking columns exist
    col_indices = ensure_tracking_columns(worksheet, headers)

    # Re-read rows after potential column additions
    rows = worksheet.get_all_values()
    headers = rows[0]

    # Check today's send count
    todays_count = count_todays_sends(rows, headers, from_email)
    print(f"\nToday's sends from {from_email}: {todays_count}")

    # Get leads to send
    follow_up_days = args.follow_up_days if args.step > 1 else None
    leads = get_leads_to_send(rows, headers, args.step, col_indices, follow_up_days)

    if not leads:
        print(f"\nNo leads eligible for step {args.step}")
        sys.exit(0)

    # Apply max_sends limit
    if args.max_sends:
        leads = leads[:args.max_sends]

    print(f"\nReady to send step {args.step} to {len(leads)} leads")
    print(f"Delay between sends: {delay_min}-{delay_max}s")

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN MODE - no emails will actually be sent")
        print("=" * 60)

    # Send loop
    sent_count = 0
    failed_count = 0
    bounced_count = 0
    start_time = time.time()

    for i, lead in enumerate(leads):
        # Render template with lead data
        rendered = render_template(template, lead)
        to_email = lead.get("email", "")
        row_num = lead["_row_num"]

        # Generate message ID
        message_id = generate_message_id(from_email, to_email, args.step)

        # Send
        print(f"\n[{i+1}/{len(leads)}] {to_email} from {from_email}")
        result = send_email_gmail_api(gmail_service, from_email, to_email,
                                       rendered["subject"], rendered["body"],
                                       message_id, dry_run=args.dry_run)

        status = result["status"]
        error = result.get("error", "")
        actual_message_id = result.get("message_id", message_id)

        if status in ("sent", "dry_run"):
            sent_count += 1
            print(f"  -> {status}")
        elif status == "bounced":
            bounced_count += 1
            print(f"  -> BOUNCED: {error[:80]}")
        else:
            failed_count += 1
            print(f"  -> FAILED: {error[:80]}")

        # Update tracking in sheet
        update_send_status(worksheet, row_num, col_indices, status,
                           from_email, args.step, actual_message_id, error)

        # Random delay between sends (skip on last send and dry runs)
        if i < len(leads) - 1 and not args.dry_run:
            delay = random.randint(delay_min, delay_max)
            print(f"  Waiting {delay}s before next send...")
            time.sleep(delay)

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"SEND COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Sent:    {sent_count}")
    print(f"  Failed:  {failed_count}")
    print(f"  Bounced: {bounced_count}")
    print(f"  Time:    {elapsed:.0f}s")
    print(f"  Step:    {args.step}")
    print(f"  Template: {args.template_name}")
    print(f"  From:    {from_email}")


if __name__ == "__main__":
    main()
