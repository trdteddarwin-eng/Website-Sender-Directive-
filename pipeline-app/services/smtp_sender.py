"""SMTP sender service — reusable HTML email sending with round-robin sender rotation.

Anti-spam measures baked in:
- List-Unsubscribe header on every email (RFC 2369, Google requirement)
- Plain-text alternative body (multipart/alternative improves deliverability)
- Minimum 60s gap between sends from the same account (send throttling)
- Unsubscribe footer injected into HTML if missing
"""

import os
import re
import sys
import json
import time
import smtplib
import html as html_mod
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

# Minimum seconds between sends from the same account
MIN_SEND_GAP_SECONDS = 60

# Track last send time per account (in-process only; resets on restart)
_last_send_time = {}


def _html_to_plain_text(html_body):
    """Strip HTML to plain text for the text/plain alternative."""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_body, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    # Collapse whitespace but keep paragraph breaks
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _ensure_unsubscribe_footer(html_body, unsub_mailto):
    """Inject an unsubscribe link at the bottom of the HTML if one isn't already there."""
    if 'unsubscribe' in html_body.lower():
        return html_body  # Already has one
    footer = (
        '<div style="margin-top:30px;padding-top:12px;border-top:1px solid #eee;'
        'font-size:11px;color:#999;text-align:center;">'
        f'<a href="mailto:{unsub_mailto}?subject=Unsubscribe" '
        'style="color:#999;text-decoration:underline;">Unsubscribe</a>'
        '</div>'
    )
    # Insert before closing </body> or </html>, or just append
    if '</body>' in html_body.lower():
        html_body = re.sub(r'(</body>)', footer + r'\1', html_body, count=1, flags=re.IGNORECASE)
    elif '</html>' in html_body.lower():
        html_body = re.sub(r'(</html>)', footer + r'\1', html_body, count=1, flags=re.IGNORECASE)
    else:
        html_body += footer
    return html_body


def _throttle_send(account_email):
    """Wait if needed to enforce minimum gap between sends from the same account."""
    last = _last_send_time.get(account_email)
    if last:
        elapsed = time.time() - last
        if elapsed < MIN_SEND_GAP_SECONDS:
            wait = MIN_SEND_GAP_SECONDS - elapsed
            print(f"[SMTP] Throttling {account_email} — waiting {wait:.0f}s")
            time.sleep(wait)
    _last_send_time[account_email] = time.time()


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


def send_email_smtp(sender_account, to_email, subject, html_body, slug=None, email_id=None):
    """Send HTML email via SMTP from a specific @tedca.online account.

    If slug is provided and html_body contains cid: image references,
    the matching screenshot files from .tmp/{slug}/ are attached inline.

    Args:
        sender_account: str (email address) or dict (account config)
        to_email: recipient email
        subject: email subject
        html_body: HTML email body
        slug: lead slug (for resolving screenshot paths)
        email_id: email UUID (for open tracking pixel injection)

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

    # ── Anti-spam: throttle sends from same account ──
    _throttle_send(acc["email"])

    sender_domain = acc["email"].split("@")[1]
    unsub_mailto = f"unsubscribe@{sender_domain}"

    msg = MIMEMultipart("related")
    msg["From"] = f"{acc.get('display_name', '')} <{acc['email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender_domain)

    # ── Anti-spam: List-Unsubscribe header (RFC 2369, required by Google) ──
    msg["List-Unsubscribe"] = f"<mailto:{unsub_mailto}?subject=Unsubscribe>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    # Inject tracking pixel URL if email_id and tracker URL are configured
    if email_id:
        from config import TRACKER_BASE_URL
        if TRACKER_BASE_URL:
            tracking_url = f"{TRACKER_BASE_URL}/.netlify/functions/track?t={email_id}"
            html_body = html_body.replace('src="cid:tracking-pixel"', f'src="{tracking_url}"')
            print(f"[SMTP] Injected tracking pixel for email {email_id}")

    # ── Anti-spam: ensure unsubscribe footer in HTML ──
    html_body = _ensure_unsubscribe_footer(html_body, unsub_mailto)

    # ── Anti-spam: multipart/alternative with plain-text + HTML ──
    # Wrapping in alternative inside the related container so inline images work
    alt_part = MIMEMultipart("alternative")
    plain_text = _html_to_plain_text(html_body)
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt_part)

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
