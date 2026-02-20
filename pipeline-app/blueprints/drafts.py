"""Drafts blueprint — GET /drafts for reviewing and sending email drafts."""

from flask import Blueprint, render_template
from services import supabase_client as db
from services.smtp_sender import get_sender_accounts

drafts_bp = Blueprint("drafts", __name__)


@drafts_bp.route("/drafts")
def drafts_page():
    try:
        # Today's queue
        todays_queue = db.get_todays_queue()
        queue_enriched = []
        for item in todays_queue:
            lead = db.get_lead_by_id(item.get("lead_id"))
            email = db.get_email_by_id(item.get("email_id"))
            queue_enriched.append({**item, "lead": lead, "email": email})

        # All pending drafts
        draft_emails = db.get_draft_emails(limit=200)
        drafts_enriched = []
        for email in draft_emails:
            lead = db.get_lead_by_id(email.get("lead_id"))
            drafts_enriched.append({**email, "lead": lead})

        # Sender accounts
        senders = get_sender_accounts()

    except Exception as e:
        print(f"[Drafts] Error loading page: {e}")
        queue_enriched = []
        drafts_enriched = []
        senders = []

    return render_template("drafts.html",
                           queue=queue_enriched,
                           drafts=drafts_enriched,
                           senders=senders)
