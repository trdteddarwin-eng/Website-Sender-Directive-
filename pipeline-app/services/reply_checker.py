"""Gmail thread polling for reply detection."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import supabase_client as db
from services.email_service import get_thread_messages, get_message_body


def check_for_replies():
    """Poll Gmail threads for replies to sent emails.

    Checks all emails with status='sent' that have a gmail_thread_id.
    If a reply is found, creates a replies row and stops the sequence.

    Returns list of newly detected replies.
    """
    sent_emails = db.get_emails_by_status("sent", limit=200)
    new_replies = []

    for email in sent_emails:
        thread_id = email.get("gmail_thread_id")
        if not thread_id:
            continue

        try:
            messages = get_thread_messages(thread_id)
        except Exception:
            continue

        # Skip if only 1 message (our sent email, no reply yet)
        if len(messages) <= 1:
            continue

        # Check for messages NOT from us (replies)
        our_msg_id = email.get("gmail_message_id")
        for msg in messages:
            if msg["id"] == our_msg_id:
                continue
            # This is a reply
            if "SENT" in msg.get("label_ids", []):
                continue  # Skip our own follow-ups

            # Check if we already recorded this reply
            existing = db.get_replies_for_lead(email["lead_id"])
            already_recorded = any(
                r.get("gmail_message_id") == msg["id"] for r in existing
            )
            if already_recorded:
                continue

            # Get full body
            try:
                body = get_message_body(msg["id"])
            except Exception:
                body = msg.get("snippet", "")

            # Simple sentiment detection
            sentiment = _detect_sentiment(body, msg.get("subject", ""))

            reply_data = {
                "lead_id": email["lead_id"],
                "email_id": email["id"],
                "gmail_message_id": msg["id"],
                "gmail_thread_id": thread_id,
                "from_email": msg.get("from", ""),
                "subject": msg.get("subject", ""),
                "body_preview": body[:500] if body else msg.get("snippet", ""),
                "body_full": body,
                "sentiment": sentiment,
                "received_at": msg.get("date"),
                "detected_at": datetime.utcnow().isoformat(),
            }

            db.create_reply(reply_data)
            db.update_email(email["id"], {"status": "replied"})

            # Stop the sequence for this lead
            seq = db.get_sequence_by_slug(email.get("slug", ""))
            if seq:
                db.update_sequence(seq["id"], {
                    "status": "stopped_reply",
                    "stopped_at": datetime.utcnow().isoformat(),
                })

            # Log activity
            db.log_activity(
                lead_id=email["lead_id"],
                slug=email.get("slug"),
                event_type="reply_detected",
                agent="reply_checker",
                message=f"Reply from {msg.get('from', 'unknown')}: {sentiment}",
                event_data={"sentiment": sentiment, "from": msg.get("from", "")},
            )

            new_replies.append(reply_data)

    return new_replies


def _detect_sentiment(body, subject):
    """Basic keyword-based sentiment detection."""
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
