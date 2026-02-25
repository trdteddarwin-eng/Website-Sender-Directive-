"""Emails blueprint — GET /emails for unified email hub."""

from flask import Blueprint, render_template
from services import supabase_client as db
from services.smtp_sender import get_sender_accounts

emails_bp = Blueprint("emails", __name__)


@emails_bp.route("/emails")
def emails_page():
    try:
        email_stats = db.get_email_stats()
    except Exception:
        email_stats = {"total": 0, "sent": 0, "opened": 0, "replied": 0, "bounced": 0,
                       "open_rate": 0, "reply_rate": 0, "bounce_rate": 0}

    try:
        senders = get_sender_accounts()
    except Exception:
        senders = []

    return render_template("emails.html", email_stats=email_stats, senders=senders)
