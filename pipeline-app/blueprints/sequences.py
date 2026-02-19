"""Sequences blueprint — GET /sequences, email sequence manager."""

from flask import Blueprint, render_template, request
from datetime import date, timedelta
from services import supabase_client as db

sequences_bp = Blueprint("sequences", __name__)


@sequences_bp.route("/sequences")
def sequences_page():
    try:
        today = date.today().isoformat()
        due_sequences = db.get_due_sequences(today)
        all_sequences = db.get_all_sequences(limit=100)

        # Build upcoming calendar (next 14 days)
        upcoming = {}
        active = db.get_active_sequences()
        for seq in active:
            nsd = seq.get("next_send_date")
            if nsd:
                upcoming.setdefault(nsd, []).append(seq)

        # Enrich due sequences with lead + email data
        for seq in due_sequences:
            lead = db.get_lead_by_id(seq.get("lead_id"))
            seq["_lead"] = lead
            touch = seq.get("current_touchpoint", 1)
            emails = db.get_emails_for_lead(seq["lead_id"]) if seq.get("lead_id") else []
            seq["_email"] = next((e for e in emails if e.get("touchpoint") == touch), None)

    except Exception:
        due_sequences = []
        all_sequences = []
        upcoming = {}

    return render_template("sequences.html",
                           due_sequences=due_sequences,
                           all_sequences=all_sequences,
                           upcoming=upcoming,
                           today=date.today().isoformat())
