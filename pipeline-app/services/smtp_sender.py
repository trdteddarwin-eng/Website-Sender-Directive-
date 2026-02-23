"""SMTP sender service — reusable HTML email sending with round-robin sender rotation."""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import supabase_client as db

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PIPELINE_APP_DIR = os.path.dirname(_THIS_DIR)
_WORKSPACE_ROOT = os.path.dirname(_PIPELINE_APP_DIR)
SMTP_ACCOUNTS_PATH = os.path.join(_WORKSPACE_ROOT, "execution", "smtp_accounts.json")


def _load_all_accounts():
    with open(SMTP_ACCOUNTS_PATH) as f:
        return json.load(f).get("accounts", [])


def get_sender_accounts():
    """Return list of active @tedca.online accounts from smtp_accounts.json."""
    return [
        a for a in _load_all_accounts()
        if a.get("active") and a["email"].endswith("@tedca.online")
    ]


def get_account_by_email(email_addr):
    """Find SMTP account config by email address."""
    for acc in _load_all_accounts():
        if acc["email"] == email_addr:
            return acc
    return None


def get_total_sends_today(queue_date=None):
    """Total emails sent today across all accounts."""
    today = (queue_date or date.today()).isoformat()
    counts = db.get_sends_per_sender_today(today)
    return sum(counts.values())


def get_next_sender(queue_date=None):
    """Round-robin: return the @tedca.online account with fewest sends today.

    Respects per-account daily_limit and global DAILY_SEND_LIMIT.
    Returns None if all accounts are at capacity or global cap is hit.
    """
    from config import DAILY_SEND_LIMIT

    accounts = get_sender_accounts()
    if not accounts:
        return None

    today = (queue_date or date.today()).isoformat()
    send_counts = db.get_sends_per_sender_today(today)

    # Check global daily cap
    total_today = sum(send_counts.values())
    if total_today >= DAILY_SEND_LIMIT:
        print(f"[SMTP] Global daily cap reached ({total_today}/{DAILY_SEND_LIMIT})")
        return None

    # Pick account with fewest sends that hasn't hit its per-account limit
    best = None
    best_count = float("inf")
    for acc in accounts:
        limit = acc.get("daily_limit", 2)
        count = send_counts.get(acc["email"], 0)
        if count >= limit:
            continue  # this account is at capacity
        if count < best_count:
            best = acc
            best_count = count

    if not best:
        print("[SMTP] All accounts at daily limit")

    return best


def send_email_smtp(sender_account, to_email, subject, html_body, slug=None):
    """Send HTML email via SMTP from a specific @tedca.online account.

    If slug is provided and html_body contains cid: image references,
    the matching screenshot files from .tmp/{slug}/ are attached inline.

    Args:
        sender_account: str (email address) or dict (account config)
        to_email: recipient email
        subject: email subject
        html_body: HTML email body
        slug: lead slug (for resolving screenshot paths)

    Returns:
        {"message_id": str, "success": bool, "error": str|None}
    """
    from email.mime.image import MIMEImage

    # Resolve account config
    if isinstance(sender_account, str):
        acc = get_account_by_email(sender_account)
        if not acc:
            return {"message_id": None, "success": False, "error": f"Account {sender_account} not found"}
    else:
        acc = sender_account

    msg = MIMEMultipart("related")
    msg["From"] = f"{acc.get('display_name', '')} <{acc['email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=acc["email"].split("@")[1])

    # HTML body
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    # Attach inline screenshots if slug provided and CID refs exist
    if slug:
        tmp_dir = os.path.join(_WORKSPACE_ROOT, ".tmp", slug)
        cid_map = {
            "old-site-screenshot": os.path.join(tmp_dir, "old-site.png"),
            "new-site-screenshot": os.path.join(tmp_dir, "new-site.png"),
        }
        for cid, filepath in cid_map.items():
            if f"cid:{cid}" in html_body and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    img = MIMEImage(f.read(), _subtype="png")
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=os.path.basename(filepath))
                msg.attach(img)
                print(f"[SMTP] Attached {os.path.basename(filepath)} as cid:{cid}")

    smtp_host = acc.get("smtp_host", "mail.privateemail.com")
    smtp_port = acc.get("smtp_port", 587)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(acc["username"], acc["password"])
            server.send_message(msg)

        print(f"[SMTP] Sent to {to_email} via {acc['email']}")
        return {"message_id": msg["Message-ID"], "success": True, "error": None}
    except Exception as e:
        print(f"[SMTP] Failed to send to {to_email} via {acc['email']}: {e}")
        return {"message_id": None, "success": False, "error": str(e)}
