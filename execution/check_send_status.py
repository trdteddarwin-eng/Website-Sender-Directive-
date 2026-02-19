#!/usr/bin/env python3
"""
Check Cold Email Sending Status

Reports on sending progress and account health:
- Emails sent today per account
- Total sent overall
- Bounce rate per account
- Daily capacity remaining
- Accounts needing attention (high bounce rate, approaching limit)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_credentials():
    """Get Google OAuth credentials."""
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


def load_accounts(config_path):
    """Load SMTP accounts config."""
    if not os.path.exists(config_path):
        return []
    with open(config_path, 'r') as f:
        data = json.load(f)
    return data.get("accounts", [])


def main():
    parser = argparse.ArgumentParser(description="Check cold email sending status and account health")
    parser.add_argument("--sheet_url", required=True, help="Google Sheet URL with leads")
    parser.add_argument("--accounts_config", default="execution/smtp_accounts.json",
                        help="Path to SMTP accounts JSON config")
    parser.add_argument("--worksheet", default=None, help="Worksheet name (default: first sheet)")
    args = parser.parse_args()

    # Load accounts config
    accounts = load_accounts(args.accounts_config)
    account_limits = {}
    for acct in accounts:
        account_limits[acct["email"]] = acct.get("daily_limit", 50)

    # Connect to sheet
    print("Connecting to Google Sheet...")
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet_id = extract_sheet_id(args.sheet_url)
    spreadsheet = client.open_by_key(sheet_id)

    if args.worksheet:
        worksheet = spreadsheet.worksheet(args.worksheet)
    else:
        worksheet = spreadsheet.sheet1

    rows = worksheet.get_all_values()
    if not rows:
        print("Sheet is empty")
        sys.exit(0)

    headers = rows[0]

    # Check for tracking columns
    required_cols = ["send_status", "send_timestamp", "sending_account", "send_step"]
    missing = [c for c in required_cols if c not in headers]
    if missing:
        print(f"Missing tracking columns: {', '.join(missing)}")
        print("Run send_cold_emails.py first to create tracking columns.")
        sys.exit(1)

    status_idx = headers.index("send_status")
    ts_idx = headers.index("send_timestamp")
    acct_idx = headers.index("sending_account")
    step_idx = headers.index("send_step")
    email_idx = headers.index("email") if "email" in headers else None
    error_idx = headers.index("send_error") if "send_error" in headers else None

    today = datetime.now().strftime("%Y-%m-%d")

    # Aggregate stats
    total_leads = len(rows) - 1
    stats = {
        "total_leads": total_leads,
        "total_sent": 0,
        "total_failed": 0,
        "total_bounced": 0,
        "total_pending": 0,
        "total_no_status": 0,
        "sent_today": 0,
    }

    per_account = defaultdict(lambda: {
        "total_sent": 0,
        "sent_today": 0,
        "bounced": 0,
        "failed": 0,
        "last_send": "",
    })

    per_step = defaultdict(int)
    recent_errors = []

    for row in rows[1:]:
        status = row[status_idx].strip() if len(row) > status_idx else ""
        timestamp = row[ts_idx].strip() if len(row) > ts_idx else ""
        account = row[acct_idx].strip() if len(row) > acct_idx else ""
        step = row[step_idx].strip() if len(row) > step_idx else ""
        error = row[error_idx].strip() if error_idx and len(row) > error_idx else ""

        if status == "sent":
            stats["total_sent"] += 1
            if timestamp.startswith(today):
                stats["sent_today"] += 1
            if account:
                per_account[account]["total_sent"] += 1
                if timestamp.startswith(today):
                    per_account[account]["sent_today"] += 1
                if not per_account[account]["last_send"] or timestamp > per_account[account]["last_send"]:
                    per_account[account]["last_send"] = timestamp
            if step:
                per_step[step] += 1

        elif status == "bounced":
            stats["total_bounced"] += 1
            if account:
                per_account[account]["bounced"] += 1

        elif status == "failed":
            stats["total_failed"] += 1
            if account:
                per_account[account]["failed"] += 1
            if error:
                email_addr = row[email_idx].strip() if email_idx and len(row) > email_idx else "?"
                recent_errors.append(f"  {email_addr}: {error[:80]}")

        elif status == "pending" or status == "":
            if status == "pending":
                stats["total_pending"] += 1
            else:
                stats["total_no_status"] += 1

        elif status == "dry_run":
            stats["total_sent"] += 1  # Count dry runs in total for capacity tracking
            if timestamp.startswith(today):
                stats["sent_today"] += 1
            if account:
                per_account[account]["total_sent"] += 1
                if timestamp.startswith(today):
                    per_account[account]["sent_today"] += 1

    # Print report
    print(f"\n{'=' * 60}")
    print(f"COLD EMAIL SEND STATUS REPORT")
    print(f"{'=' * 60}")
    print(f"Date: {today}")
    print(f"Sheet: {args.sheet_url}")

    print(f"\n--- Overall ---")
    print(f"  Total leads:     {stats['total_leads']}")
    print(f"  Sent (all time): {stats['total_sent']}")
    print(f"  Sent today:      {stats['sent_today']}")
    print(f"  Failed:          {stats['total_failed']}")
    print(f"  Bounced:         {stats['total_bounced']}")
    print(f"  Pending/Unsent:  {stats['total_pending'] + stats['total_no_status']}")

    bounce_rate = (stats['total_bounced'] / max(stats['total_sent'], 1)) * 100
    print(f"  Bounce rate:     {bounce_rate:.1f}%")

    if per_step:
        print(f"\n--- By Sequence Step ---")
        for step in sorted(per_step.keys()):
            print(f"  Step {step}: {per_step[step]} sent")

    print(f"\n--- Per Account ---")
    print(f"  {'Account':<35} {'Today':>6} {'Total':>6} {'Bounce':>7} {'Limit':>6} {'Remaining':>10}")
    print(f"  {'-' * 35} {'-' * 6} {'-' * 6} {'-' * 7} {'-' * 6} {'-' * 10}")

    total_remaining = 0
    alerts = []

    all_account_emails = set(per_account.keys()) | set(account_limits.keys())
    for email in sorted(all_account_emails):
        acct_data = per_account.get(email, {"total_sent": 0, "sent_today": 0, "bounced": 0, "failed": 0})
        limit = account_limits.get(email, 50)
        remaining = max(0, limit - acct_data["sent_today"])
        total_remaining += remaining

        bounce_pct = (acct_data["bounced"] / max(acct_data["total_sent"], 1)) * 100

        print(f"  {email:<35} {acct_data['sent_today']:>6} {acct_data['total_sent']:>6} {bounce_pct:>6.1f}% {limit:>6} {remaining:>10}")

        # Flag accounts needing attention
        if bounce_pct > 2.0 and acct_data["total_sent"] > 10:
            alerts.append(f"  HIGH BOUNCE: {email} ({bounce_pct:.1f}% bounce rate) — consider pausing")
        if acct_data["sent_today"] >= limit:
            alerts.append(f"  AT LIMIT: {email} — daily limit reached ({limit})")

    print(f"\n  Total daily capacity remaining: {total_remaining}")

    if alerts:
        print(f"\n--- Alerts ---")
        for alert in alerts:
            print(alert)

    if recent_errors:
        print(f"\n--- Recent Errors (last {min(len(recent_errors), 10)}) ---")
        for err in recent_errors[-10:]:
            print(err)

    print()


if __name__ == "__main__":
    main()
