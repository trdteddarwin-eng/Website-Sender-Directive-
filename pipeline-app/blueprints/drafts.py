"""Drafts blueprint — GET /drafts for reviewing and sending email drafts."""

from flask import Blueprint, render_template
from services import supabase_client as db
from services.smtp_sender import get_sender_accounts

drafts_bp = Blueprint("drafts", __name__)


@drafts_bp.route("/drafts")
def drafts_page():
    # Today's queue (may not exist yet)
    queue_enriched = []
    try:
        todays_queue = db.get_todays_queue()
        for item in todays_queue:
            lead = db.get_lead_by_id(item.get("lead_id"))
            email = db.get_email_by_id(item.get("email_id"))
            queue_enriched.append({**item, "lead": lead, "email": email})
    except Exception as e:
        print(f"[Drafts] Queue table not available: {e}")

    # All pending drafts
    drafts_enriched = []
    try:
        draft_emails = db.get_draft_emails(limit=200)
        for email in draft_emails:
            lead = db.get_lead_by_id(email.get("lead_id"))
            drafts_enriched.append({**email, "lead": lead})
    except Exception as e:
        print(f"[Drafts] Error loading drafts: {e}")

    # Sender accounts
    try:
        senders = get_sender_accounts()
    except Exception as e:
        print(f"[Drafts] Error loading senders: {e}")
        senders = []

    return render_template("drafts.html",
                           queue=queue_enriched,
                           drafts=drafts_enriched,
                           senders=senders)
