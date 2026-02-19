"""API blueprint — all JSON API endpoints."""

import os
import json
from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify

from services import supabase_client as db
from services.sse_manager import sse
from config import TMP_DIR

api_bp = Blueprint("api", __name__)


# ── Pipeline ───────────────────────────────────────────

@api_bp.route("/api/pipeline/run", methods=["POST"])
def run_pipeline():
    """Start pipeline for next unprocessed lead or a specific slug."""
    data = request.get_json(silent=True) or {}
    slug = data.get("slug")

    if slug:
        lead = db.get_lead_by_slug(slug)
    else:
        lead = db.get_next_unprocessed_lead()

    if not lead:
        return jsonify({"error": "No unprocessed leads found"}), 404

    try:
        from services.pipeline_runner import start_pipeline
        run = start_pipeline(lead)
        return jsonify({"ok": True, "run_id": run["id"], "slug": lead["slug"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/pipeline/run-batch", methods=["POST"])
def run_batch():
    """Start pipeline for multiple leads."""
    data = request.get_json(silent=True) or {}
    count = min(data.get("count", 1), 10)

    results = []
    for _ in range(count):
        lead = db.get_next_unprocessed_lead()
        if not lead:
            break
        try:
            from services.pipeline_runner import start_pipeline
            run = start_pipeline(lead)
            results.append({"slug": lead["slug"], "run_id": run["id"]})
        except Exception as e:
            results.append({"slug": lead.get("slug", "?"), "error": str(e)})

    return jsonify({"ok": True, "started": len(results), "results": results})


@api_bp.route("/api/pipeline/status")
def pipeline_status():
    """Get current pipeline run status."""
    try:
        run = db.get_active_pipeline_run()
    except Exception:
        return jsonify({"active": False, "error": "Data source not configured"})
    if not run:
        return jsonify({"active": False})
    lead = db.get_lead_by_id(run.get("lead_id")) if run.get("lead_id") else None
    return jsonify({
        "active": True,
        "run": run,
        "lead": lead,
    })


# ── Leads ──────────────────────────────────────────────

@api_bp.route("/api/leads/import", methods=["POST"])
def import_leads():
    """Import leads from a JSON file."""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath", "")

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        from services.lead_importer import import_leads_from_file
        imported, skipped, errors = import_leads_from_file(filepath)
        return jsonify({
            "ok": True,
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:10],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/leads/<slug>/research")
def get_research(slug):
    """Get research.json for a lead."""
    research_path = os.path.join(TMP_DIR, slug, "research.json")
    if os.path.exists(research_path):
        with open(research_path) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No research data found"}), 404


# ── Emails / Sequences ────────────────────────────────

@api_bp.route("/api/emails/<email_id>/send", methods=["POST"])
def send_email(email_id):
    """Send a Gmail draft."""
    email = db.get_email_by_id(email_id)

    if not email:
        return jsonify({"error": "Email not found"}), 404

    draft_id = email.get("gmail_draft_id")
    if not draft_id:
        return jsonify({"error": "No Gmail draft ID — create draft first"}), 400

    try:
        from services.email_service import send_draft
        result = send_draft(draft_id)

        # Update email status
        db.update_email(email_id, {
            "status": "sent",
            "gmail_message_id": result.get("message_id", ""),
            "gmail_thread_id": result.get("thread_id", ""),
            "sent_at": datetime.utcnow().isoformat(),
        })

        # Advance sequence
        seq = db.get_sequence_by_slug(email.get("slug", ""))
        if seq:
            touch = email.get("touchpoint", 1)
            if touch >= 4:
                db.update_sequence(seq["id"], {
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                })
            else:
                days = {1: 3, 2: 4, 3: 7}
                next_date = (datetime.utcnow() + timedelta(days=days.get(touch, 3))).strftime("%Y-%m-%d")
                db.update_sequence(seq["id"], {
                    "current_touchpoint": touch + 1,
                    "next_send_date": next_date,
                })

        # Log
        db.log_activity(
            lead_id=email.get("lead_id"), slug=email.get("slug"),
            event_type="email_sent", agent="user",
            message=f"Touch {email.get('touchpoint', 1)} sent: {email.get('subject', '')}",
        )
        sse.publish("email_sent", {"email_id": email_id, "slug": email.get("slug")})

        return jsonify({"ok": True, "message_id": result.get("message_id")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/emails/<email_id>/skip", methods=["POST"])
def skip_email(email_id):
    """Skip a scheduled email."""
    db.update_email(email_id, {"status": "skipped"})
    return jsonify({"ok": True})


@api_bp.route("/api/emails/<email_id>/preview")
def preview_email(email_id):
    """Get email HTML content for preview."""
    email = db.get_email_by_id(email_id)

    if not email:
        return jsonify({"error": "Email not found"}), 404

    return jsonify({
        "subject": email.get("subject", ""),
        "html": email.get("html_content", ""),
        "status": email.get("status", ""),
        "touchpoint": email.get("touchpoint", 1),
    })


@api_bp.route("/api/sequences/<seq_id>/pause", methods=["POST"])
def pause_sequence(seq_id):
    db.update_sequence(seq_id, {"status": "paused", "paused_at": datetime.utcnow().isoformat()})
    return jsonify({"ok": True})


@api_bp.route("/api/sequences/<seq_id>/resume", methods=["POST"])
def resume_sequence(seq_id):
    db.update_sequence(seq_id, {"status": "active", "paused_at": None})
    return jsonify({"ok": True})


# ── Settings ───────────────────────────────────────────

@api_bp.route("/api/settings/test-supabase")
@api_bp.route("/api/settings/test-sheets")
def test_sheets():
    try:
        counts = db.get_lead_counts()
        return jsonify({"ok": True, "lead_count": counts.get("total", 0)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@api_bp.route("/api/settings/test-gmail")
def test_gmail():
    try:
        from services.email_service import check_gmail_auth
        return jsonify(check_gmail_auth())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── Preview ────────────────────────────────────────────

@api_bp.route("/api/preview/<slug>")
def preview_spec_site(slug):
    """Serve the spec site HTML for iframe preview."""
    html_path = os.path.join(TMP_DIR, slug, "index.html")
    if os.path.exists(html_path):
        with open(html_path) as f:
            return f.read(), 200, {"Content-Type": "text/html"}
    return "Not found", 404
