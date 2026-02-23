#!/usr/bin/env python3
"""
Domain Warming Script — tedca.online

Sends natural-sounding emails between internal accounts to warm the domain
before cold outreach. Reuses SMTP logic from send_cold_emails.py.

Usage:
    python execution/warm_domain_emails.py --dry-run    # test config
    python execution/warm_domain_emails.py              # send warming emails
"""

import os
import sys
import json
import argparse
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ACCOUNTS_PATH = os.path.join(SCRIPT_DIR, "smtp_accounts.json")

# 5 warming emails: natural business conversations between teammates
WARMING_EMAILS = [
    {
        "from": "john@tedca.online",
        "to": "patrick@tedca.online",
        "subject": "Quick question about the client deck",
        "body": (
            "Hey Patrick,\n\n"
            "Do you have the latest version of the client presentation? "
            "I want to review the updated numbers before our call tomorrow morning.\n\n"
            "Also, let me know if you need anything from my side for the quarterly review.\n\n"
            "Thanks,\n"
            "John"
        ),
    },
    {
        "from": "john@tedca.online",
        "to": "ted@tedca.online",
        "subject": "Re: Team sync this week",
        "body": (
            "Hey Ted,\n\n"
            "Just confirming I'm good for the team sync on Thursday at 2pm. "
            "I'll have the project status update ready to share.\n\n"
            "One thing — can we add 10 minutes to discuss the new onboarding process? "
            "I have a few ideas that might streamline things.\n\n"
            "Talk soon,\n"
            "John"
        ),
    },
    {
        "from": "patrick@tedca.online",
        "to": "john@tedca.online",
        "subject": "Re: Quick question about the client deck",
        "body": (
            "Hey John,\n\n"
            "Yeah, I just finished updating it this afternoon. I'll drop the link in "
            "our shared drive by end of day.\n\n"
            "For the quarterly review, I think we're all set on my end. "
            "Just need final sign-off on the budget numbers.\n\n"
            "Best,\n"
            "Patrick"
        ),
    },
    {
        "from": "patrick@tedca.online",
        "to": "ted@tedca.online",
        "subject": "Lunch plans Friday?",
        "body": (
            "Hey Ted,\n\n"
            "A few of us are grabbing lunch Friday around noon. Want to join? "
            "Thinking that new Mediterranean place on 5th.\n\n"
            "Also, nice work on the proposal — client seemed really impressed "
            "during the walkthrough.\n\n"
            "Cheers,\n"
            "Patrick"
        ),
    },
    {
        "from": "ted@tedca.online",
        "to": "john@tedca.online",
        "subject": "Re: Team sync this week",
        "body": (
            "Hey John,\n\n"
            "Thursday at 2pm works. And yes, absolutely — let's add the onboarding "
            "discussion. I've been thinking about that too.\n\n"
            "I'll send out an updated agenda tomorrow morning. "
            "See you then.\n\n"
            "Best,\n"
            "Ted"
        ),
    },
]


def load_accounts(config_path):
    """Load tedca.online SMTP accounts from the shared config."""
    with open(config_path, "r") as f:
        data = json.load(f)

    # Filter to only tedca.online accounts
    accounts = {
        a["email"]: a
        for a in data["accounts"]
        if a["email"].endswith("@tedca.online") and a.get("active", True)
    }

    if not accounts:
        print("Error: No active tedca.online accounts found in config")
        sys.exit(1)

    print(f"Loaded {len(accounts)} tedca.online accounts: {', '.join(accounts.keys())}")
    return accounts


def send_email(account, to_email, subject, body, dry_run=False):
    """Send a single email via SMTP. Returns dict with status."""
    from_label = f"{account['display_name']} <{account['email']}>"

    if dry_run:
        print(f"  [DRY RUN] {account['email']} -> {to_email}")
        print(f"    Subject: {subject}")
        print(f"    Body: {body[:80]}...")
        return {"status": "dry_run"}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = from_label
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(account["smtp_host"], account["smtp_port"]) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(account["username"], account["password"])
            server.send_message(msg)

        return {"status": "sent"}

    except smtplib.SMTPAuthenticationError as e:
        return {"status": "auth_error", "error": str(e)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Domain warming for tedca.online accounts")
    parser.add_argument(
        "--accounts-config",
        default=DEFAULT_ACCOUNTS_PATH,
        help="Path to smtp_accounts.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test SMTP auth without sending emails",
    )
    parser.add_argument(
        "--delay-min",
        type=int,
        default=30,
        help="Minimum delay between sends in seconds (default: 30)",
    )
    parser.add_argument(
        "--delay-max",
        type=int,
        default=90,
        help="Maximum delay between sends in seconds (default: 90)",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("TEDCA.ONLINE DOMAIN WARMING")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 50)

    # Load accounts
    accounts = load_accounts(args.accounts_config)

    # Verify all sender accounts exist in config
    senders = set(e["from"] for e in WARMING_EMAILS)
    missing = senders - set(accounts.keys())
    if missing:
        print(f"Error: Missing accounts in config: {missing}")
        sys.exit(1)

    # Send warming emails
    sent = 0
    failed = 0

    for i, email in enumerate(WARMING_EMAILS):
        sender = accounts[email["from"]]
        to = email["to"]
        subject = email["subject"]
        body = email["body"]

        print(f"\n[{i+1}/{len(WARMING_EMAILS)}] {email['from']} -> {to}")
        print(f"  Subject: {subject}")

        result = send_email(sender, to, subject, body, dry_run=args.dry_run)

        if result["status"] in ("sent", "dry_run"):
            sent += 1
            print(f"  -> {result['status']}")
        else:
            failed += 1
            print(f"  -> {result['status'].upper()}: {result.get('error', '')[:100]}")

        # Delay between sends (skip after last email)
        if i < len(WARMING_EMAILS) - 1:
            if args.dry_run:
                print(f"  (would wait {args.delay_min}-{args.delay_max}s)")
            else:
                delay = random.randint(args.delay_min, args.delay_max)
                print(f"  Waiting {delay}s...")
                time.sleep(delay)

    # Summary
    print(f"\n{'=' * 50}")
    print(f"WARMING COMPLETE")
    print(f"  Sent: {sent}  |  Failed: {failed}")
    print(f"{'=' * 50}")

    if failed > 0:
        print("\nSome emails failed. Check errors above.")
        print("If auth_error: you likely need Google App Passwords (not regular password).")
        print("  -> Go to Google Account > Security > 2-Step Verification > App Passwords")
        sys.exit(1)


if __name__ == "__main__":
    main()
