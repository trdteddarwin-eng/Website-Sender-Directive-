"""Daily queue service — generates and manages the daily outreach queue."""

import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import supabase_client as db
from services.smtp_sender import get_sender_accounts, get_next_sender, send_email_smtp


def generate_daily_queue(count=6):
    """Pick top N hot leads with draft touch-1 emails, assign senders round-robin.

    Selection priority:
    1. Leads with tier='hot' and pipeline_status='completed'
    2. Have a touch-1 email in status='draft'
    3. Not already in today's queue
    4. Ordered by created_at (oldest first)

    Returns list of queued items.
    """
    today = date.today().isoformat()
    existing_queue = db.get_todays_queue()
    already_queued_lead_ids = {item["lead_id"] for item in existing_queue}

    # Get draft touch-1 emails
    draft_emails = db.get_draft_emails(limit=200)
    touch1_drafts = [
        e for e in draft_emails
        if e.get("touchpoint") == 1
        and e.get("lead_id") not in already_queued_lead_ids
    ]

    # Get lead details and filter to hot + completed
    candidates = []
    for email in touch1_drafts:
        lead = db.get_lead_by_id(email["lead_id"])
        if not lead:
            continue
        if lead.get("lead_tier") == "hot" and lead.get("pipeline_status") == "completed":
            candidates.append((lead, email))

    # Sort by created_at ascending (oldest first)
    candidates.sort(key=lambda x: x[0].get("created_at", ""))

    # Take top N
    selected = candidates[:count]

    # Assign senders round-robin
    senders = get_sender_accounts()
    if not senders:
        return []

    queued_items = []
    for i, (lead, email) in enumerate(selected):
        sender = senders[i % len(senders)]
        item = db.create_queue_item({
            "queue_date": today,
            "lead_id": lead["id"],
            "slug": lead["slug"],
            "sender_account": sender["email"],
            "email_id": email["id"],
            "status": "queued",
        })
        queued_items.append(item)

    return queued_items


def get_todays_queue():
    """Return today's queue with lead + email details."""
    items = db.get_todays_queue()
    enriched = []
    for item in items:
        lead = db.get_lead_by_id(item.get("lead_id"))
        email = db.get_email_by_id(item.get("email_id"))
        enriched.append({
            **item,
            "lead": lead,
            "email": email,
        })
    return enriched


def approve_and_send_all():
    """Send all 'queued' items in today's queue via SMTP.

    Returns {sent: N, failed: N, errors: [...]}
    """
    items = db.get_todays_queue()
    queued = [i for i in items if i.get("status") == "queued"]

    sent = 0
    failed = 0
    errors = []

    for item in queued:
        result = _send_queue_item(item)
        if result["success"]:
            sent += 1
        else:
            failed += 1
            errors.append({"queue_id": item["id"], "error": result["error"]})

    return {"sent": sent, "failed": failed, "errors": errors}


def approve_and_send_one(queue_id):
    """Send a single queued item."""
    item = db.get_queue_item(queue_id)
    if not item:
        return {"success": False, "error": "Queue item not found"}
    if item.get("status") != "queued":
        return {"success": False, "error": f"Item status is '{item.get('status')}', not 'queued'"}
    return _send_queue_item(item)


def _send_queue_item(item):
    """Internal: send a single queue item via SMTP."""
    email = db.get_email_by_id(item.get("email_id"))
    if not email:
        return {"success": False, "error": "Email not found"}

    lead = db.get_lead_by_id(item.get("lead_id"))
    to_email = email.get("to_email") or (lead.get("email") if lead else "")
    if not to_email:
        return {"success": False, "error": "No recipient email"}

    sender = item.get("sender_account")
    subject = email.get("subject", "")
    html_body = email.get("html_content", "")

    result = send_email_smtp(sender, to_email, subject, html_body)

    now = datetime.utcnow().isoformat()

    if result["success"]:
        db.update_queue_item(item["id"], {
            "status": "sent",
            "approved_at": now,
            "sent_at": now,
        })
        db.update_email(item["email_id"], {
            "status": "sent",
            "sent_at": now,
            "sender_account": sender,
            "sent_via": "smtp",
        })

        # Advance sequence
        seq = db.get_sequence_by_slug(item.get("slug", ""))
        if seq:
            touch = email.get("touchpoint", 1)
            if touch >= 4:
                db.update_sequence(seq["id"], {
                    "status": "completed",
                    "completed_at": now,
                })
            else:
                from datetime import timedelta
                days = {1: 3, 2: 4, 3: 7}
                next_date = (datetime.utcnow() + timedelta(days=days.get(touch, 3))).strftime("%Y-%m-%d")
                db.update_sequence(seq["id"], {
                    "current_touchpoint": touch + 1,
                    "next_send_date": next_date,
                })

        # Log activity
        db.log_activity(
            lead_id=item.get("lead_id"), slug=item.get("slug"),
            event_type="email_sent", agent="queue",
            message=f"Touch {email.get('touchpoint', 1)} sent via {sender}: {subject}",
        )
    else:
        db.update_queue_item(item["id"], {"status": "failed"})

    return result


def reassign_sender(queue_id, new_sender_account):
    """Change which inbox sends this email."""
    db.update_queue_item(queue_id, {"sender_account": new_sender_account})
    return db.get_queue_item(queue_id)


def skip_queue_item(queue_id):
    """Mark as skipped."""
    db.update_queue_item(queue_id, {"status": "skipped"})
    return db.get_queue_item(queue_id)
