"""Auto-reply service — detects lead replies, generates AI responses, sends or drafts."""

import os
import sys
import json
import smtplib
import uuid
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import supabase_client as db
from services.inbox_service import get_tedca_accounts, fetch_message_body

# Path to execution scripts
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PIPELINE_APP_DIR = os.path.dirname(_THIS_DIR)
_WORKSPACE_ROOT = os.path.dirname(_PIPELINE_APP_DIR)
SMTP_ACCOUNTS_PATH = os.path.join(_WORKSPACE_ROOT, "execution", "smtp_accounts.json")

sys.path.insert(0, os.path.join(_WORKSPACE_ROOT, "execution"))
from generate_reply_email import generate_reply


def _load_smtp_accounts():
    with open(SMTP_ACCOUNTS_PATH) as f:
        return json.load(f).get("accounts", [])


def _get_account_by_email(email_addr):
    """Find SMTP account config by email address."""
    for acc in _load_smtp_accounts():
        if acc["email"] == email_addr:
            return acc
    return None


def _detect_sentiment(body, subject):
    """Basic keyword-based sentiment detection (same as reply_checker.py)."""
    text = (body + " " + subject).lower()

    ooo_keywords = ["out of office", "out of the office", "auto-reply", "automatic reply",
                     "on vacation", "away from", "currently unavailable"]
    if any(k in text for k in ooo_keywords):
        return "out_of_office"

    positive_keywords = ["interested", "sounds good", "let's chat", "let's talk",
                         "schedule a call", "love to", "would like", "tell me more",
                         "great work", "impressive", "set up a time", "free this week",
                         "yes", "absolutely"]
    negative_keywords = ["not interested", "no thanks", "remove me", "unsubscribe",
                         "stop emailing", "do not contact", "no thank you",
                         "already have", "not looking", "please remove"]

    neg_count = sum(1 for k in negative_keywords if k in text)
    pos_count = sum(1 for k in positive_keywords if k in text)

    if neg_count > pos_count:
        return "negative"
    if pos_count > 0:
        return "positive"
    return "neutral"


def _find_lead_for_email(from_email):
    """Match an incoming email address to a known lead we've emailed.

    Scans emails.json for sent emails, finds the lead_id, then looks up
    the lead in the sheet to verify the email matches.

    Returns (lead, email_record) or (None, None).
    """
    from_email_lower = from_email.lower().strip()

    # Get all leads and check if this email matches any
    # First try direct lead lookup by email
    sb = db._get_client()
    lead_result = sb.table("leads").select("*").ilike("email", from_email_lower).limit(1).execute()
    if lead_result.data:
        lead = db._add_lead_aliases(lead_result.data[0])
        # Find a sent email for this lead
        emails = db.get_emails_by_lead_and_statuses(lead["id"], ["sent", "opened", "replied"])
        if emails:
            return lead, emails[0]

    return None, None


def process_new_email(account_email, uid, from_email, subject):
    """Process a new incoming email for potential auto-reply.

    Args:
        account_email: Our tedca.online email that received this
        uid: IMAP UID of the incoming message
        from_email: Sender's email address
        subject: Email subject line

    Returns:
        dict with result info, or None if skipped
    """
    # Dedup check
    existing = db.get_auto_reply_by_uid(uid)
    if existing:
        return None

    # Match sender to a known lead
    lead, original_email = _find_lead_for_email(from_email)
    if not lead:
        return None  # Not a lead we've emailed — ignore

    # Get account object for IMAP/SMTP
    account_obj = _get_account_by_email(account_email)
    if not account_obj:
        print(f"[AutoReply] Account {account_email} not found in smtp_accounts.json")
        return None

    # Fetch full body
    try:
        msg_data = fetch_message_body(account_obj, uid)
        if not msg_data:
            print(f"[AutoReply] Could not fetch body for UID {uid}")
            return None
    except Exception as e:
        print(f"[AutoReply] Error fetching body for UID {uid}: {e}")
        return None

    body_text = msg_data.get("text", "") or ""
    body_html = msg_data.get("html", "") or ""
    incoming_message_id = msg_data.get("message_id", "")

    # Use text body for analysis, fall back to stripping HTML
    analysis_text = body_text
    if not analysis_text and body_html:
        import re
        analysis_text = re.sub(r"<[^>]+>", " ", body_html)
        analysis_text = re.sub(r"\s+", " ", analysis_text).strip()

    # Detect sentiment
    sentiment = _detect_sentiment(analysis_text, subject)

    # Handle out-of-office
    if sentiment == "out_of_office":
        record = {
            "lead_id": lead["id"],
            "slug": lead.get("slug", ""),
            "account": account_email,
            "incoming_uid": uid,
            "incoming_from": from_email,
            "incoming_subject": subject,
            "incoming_body_preview": analysis_text[:200],
            "sentiment": "out_of_office",
            "reply_subject": None,
            "reply_body": None,
            "status": "skipped_ooo",
            "sent_at": None,
        }
        db.create_auto_reply(record)
        db.log_activity(
            lead_id=lead["id"], slug=lead.get("slug"),
            event_type="auto_reply_skipped_ooo", agent="auto_reply",
            message=f"Out-of-office from {from_email}, skipped",
        )
        return {"action": "skipped_ooo", "lead_id": lead["id"], "slug": lead.get("slug")}

    # Generate AI reply
    sender_name = account_obj.get("display_name", "Ted")
    original_subject = original_email.get("subject", subject) if original_email else subject
    original_snippet = ""
    if original_email:
        original_snippet = original_email.get("text_preview", "")[:200]

    try:
        reply_result = generate_reply(
            lead_name=lead.get("first_name") or lead.get("full_name", ""),
            company=lead.get("company_name", ""),
            reply_text=analysis_text,
            original_subject=original_subject,
            original_snippet=original_snippet,
            sentiment=sentiment,
            sender_name=sender_name,
        )
    except Exception as e:
        print(f"[AutoReply] Reply generation failed: {e}")
        reply_result = {"reply_subject": f"Re: {subject}", "reply_body": ""}

    reply_subject = reply_result.get("reply_subject", f"Re: {subject}")
    reply_body = reply_result.get("reply_body", "")

    if not reply_body:
        print(f"[AutoReply] Empty reply body for {from_email}, saving as draft")
        sentiment = "neutral"  # Force to draft

    # Decide: send or draft
    if sentiment == "positive" and reply_body:
        # Auto-send immediately
        try:
            send_reply_smtp(
                account_obj, from_email, reply_subject, reply_body,
                in_reply_to_msgid=incoming_message_id,
            )
            status = "sent"
            sent_at = datetime.utcnow().isoformat()
        except Exception as e:
            print(f"[AutoReply] SMTP send failed: {e}")
            status = "failed"
            sent_at = None
    else:
        # Save as draft for review
        status = "draft"
        sent_at = None

    # Record in auto_replies
    record = {
        "lead_id": lead["id"],
        "slug": lead.get("slug", ""),
        "account": account_email,
        "incoming_uid": uid,
        "incoming_from": from_email,
        "incoming_subject": subject,
        "incoming_body_preview": analysis_text[:200],
        "sentiment": sentiment,
        "reply_subject": reply_subject,
        "reply_body": reply_body,
        "status": status,
        "sent_at": sent_at,
    }
    db.create_auto_reply(record)

    # Update original email status to "replied" and stop sequence
    if original_email and status == "sent":
        db.update_email(original_email["id"], {"status": "replied"})
        seq = db.get_sequence_by_slug(lead.get("slug", ""))
        if seq:
            db.update_sequence(seq["id"], {
                "status": "stopped_reply",
                "stopped_at": datetime.utcnow().isoformat(),
            })

    # Log activity
    action_str = "auto-sent" if status == "sent" else ("drafted" if status == "draft" else "failed")
    db.log_activity(
        lead_id=lead["id"], slug=lead.get("slug"),
        event_type=f"auto_reply_{status}",
        agent="auto_reply",
        message=f"Auto-reply {action_str} to {from_email} ({sentiment})",
        event_data={"sentiment": sentiment, "status": status},
    )

    return {
        "action": status,
        "lead_id": lead["id"],
        "slug": lead.get("slug", ""),
        "sentiment": sentiment,
        "from_email": from_email,
        "subject": subject,
    }


def send_reply_smtp(account_obj, to_email, subject, body, in_reply_to_msgid=None):
    """Send a plain-text reply via SMTP.

    Args:
        account_obj: dict from smtp_accounts.json with smtp_host, smtp_port, username, password, etc.
        to_email: Recipient email
        subject: Reply subject line
        body: Plain text body
        in_reply_to_msgid: Optional Message-ID for threading
    """
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f"{account_obj.get('display_name', '')} <{account_obj['email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=account_obj["email"].split("@")[1])

    if in_reply_to_msgid:
        msg["In-Reply-To"] = in_reply_to_msgid
        msg["References"] = in_reply_to_msgid

    smtp_host = account_obj.get("smtp_host", "mail.privateemail.com")
    smtp_port = account_obj.get("smtp_port", 587)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(account_obj["username"], account_obj["password"])
        server.send_message(msg)

    print(f"[AutoReply] Sent reply to {to_email} via {account_obj['email']}")


def send_draft_reply(auto_reply_id, edited_body=None):
    """Manually send a previously drafted auto-reply.

    Args:
        auto_reply_id: ID of the auto_reply record
        edited_body: Optional edited body text (overrides stored draft)

    Returns:
        Updated auto_reply record or None
    """
    record = db.get_auto_reply_by_id(auto_reply_id)
    if not record:
        return None
    if record.get("status") != "draft":
        return None

    account_obj = _get_account_by_email(record["account"])
    if not account_obj:
        return None

    body = edited_body if edited_body else record.get("reply_body", "")
    subject = record.get("reply_subject", "Re: ")

    # Fetch the original message's Message-ID for threading
    in_reply_to = None
    try:
        msg_data = fetch_message_body(account_obj, record["incoming_uid"])
        if msg_data:
            in_reply_to = msg_data.get("message_id")
    except Exception:
        pass

    try:
        send_reply_smtp(account_obj, record["incoming_from"], subject, body,
                        in_reply_to_msgid=in_reply_to)
    except Exception as e:
        db.update_auto_reply(auto_reply_id, {"status": "failed"})
        raise e

    now = datetime.utcnow().isoformat()
    db.update_auto_reply(auto_reply_id, {
        "status": "sent",
        "sent_at": now,
        "reply_body": body,  # Save edited body if changed
    })

    # Stop sequence for this lead
    lead = db.get_lead_by_id(record.get("lead_id"))
    if lead:
        seq = db.get_sequence_by_slug(lead.get("slug", ""))
        if seq:
            db.update_sequence(seq["id"], {
                "status": "stopped_reply",
                "stopped_at": now,
            })

    # Update original email status
    sent_emails = db.get_emails_by_lead_and_statuses(record.get("lead_id"), ["sent", "opened"])
    if sent_emails:
        db.update_email(sent_emails[0]["id"], {"status": "replied"})

    db.log_activity(
        lead_id=record.get("lead_id"), slug=record.get("slug"),
        event_type="auto_reply_sent",
        agent="user",
        message=f"Draft reply sent to {record['incoming_from']}",
    )

    return db.get_auto_reply_by_id(auto_reply_id)
