"""Senders blueprint — GET /senders for sender account dashboard."""

from datetime import date
from flask import Blueprint, render_template
from services import supabase_client as db
from services.smtp_sender import get_sender_accounts, get_total_sends_today
from config import DAILY_SEND_LIMIT

senders_bp = Blueprint("senders", __name__)


@senders_bp.route("/senders")
def senders_page():
    try:
        accounts = get_sender_accounts()
    except Exception:
        accounts = []

    today = date.today().isoformat()
    try:
        send_counts = db.get_sends_per_sender_today(today)
    except Exception:
        send_counts = {}

    total_sent = sum(send_counts.values())

    try:
        performance = db.get_sender_performance()
    except Exception:
        performance = {}

    sender_cards = []
    for acc in accounts:
        email = acc["email"]
        sent_today = send_counts.get(email, 0)
        limit = acc.get("daily_limit", 2)
        perf = performance.get(email, {"sent": 0, "opened": 0, "replied": 0, "open_rate": 0, "reply_rate": 0})
        sender_cards.append({
            "email": email,
            "display_name": acc.get("display_name", ""),
            "daily_limit": limit,
            "sent_today": sent_today,
            "total_sent": perf.get("sent", 0),
            "opened": perf.get("opened", 0),
            "replied": perf.get("replied", 0),
            "open_rate": perf.get("open_rate", 0),
            "reply_rate": perf.get("reply_rate", 0),
        })

    return render_template("senders.html",
                           sender_cards=sender_cards,
                           total_sent_today=total_sent,
                           daily_limit=DAILY_SEND_LIMIT,
                           remaining=max(0, DAILY_SEND_LIMIT - total_sent))
