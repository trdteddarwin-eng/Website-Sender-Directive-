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


@api_bp.route("/api/pipeline/resume", methods=["POST"])
def resume_pipeline():
    """Resume a failed pipeline run from where it left off."""
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id")
    if not run_id:
        return jsonify({"error": "run_id is required"}), 400
    try:
        from services.pipeline_runner import resume_pipeline as _resume
        run = _resume(run_id)
        return jsonify({"ok": True, "run_id": run["id"], "slug": run.get("slug")})
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
    """Get current pipeline run status (active or most recent)."""
    try:
        run = db.get_active_pipeline_run()
    except Exception:
        return jsonify({"active": False, "error": "Data source not configured"})

    if run:
        lead = db.get_lead_by_id(run.get("lead_id")) if run.get("lead_id") else None
        return jsonify({"active": True, "run": run, "lead": lead})

    # No active run — return most recent run so UI can show last state
    try:
        recent = db.get_recent_pipeline_runs(limit=1)
        if recent:
            last_run = recent[0]
            lead = db.get_lead_by_id(last_run.get("lead_id")) if last_run.get("lead_id") else None
            return jsonify({"active": False, "last_run": last_run, "lead": lead})
    except Exception:
        pass

    return jsonify({"active": False})


# ── Leads ──────────────────────────────────────────────

@api_bp.route("/api/leads", methods=["POST"])
def create_lead():
    """Create a new lead."""
    data = request.get_json(silent=True) or {}
    company_name = data.get("company_name", "").strip()
    if not company_name:
        return jsonify({"error": "company_name is required"}), 400

    import re
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.split(",")[0].strip().lower()).strip("-")
    if not slug:
        return jsonify({"error": "Invalid company name"}), 400

    import uuid
    lead_data = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lead.{slug}")),
        "slug": slug,
        "company_name": company_name,
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "website": data.get("website", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
        "industry": data.get("industry", "HVAC"),
        "lead_tier": data.get("lead_tier", "cold"),
        "lead_score": int(data.get("lead_score", 0) or 0),
        "pipeline_status": "pending",
        "is_qualified": True,
    }
    try:
        result = db.upsert_lead(lead_data)
        return jsonify({"ok": True, "lead": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/leads/search")
def search_leads():
    """Quick lead search by name/slug for typeahead."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"ok": True, "leads": []})
    leads, _ = db.get_leads(search=q, sort_by="lead_score", sort_dir="desc", page=1, per_page=10)
    return jsonify({"ok": True, "leads": [
        {"slug": l["slug"], "company_name": l.get("company_name", l["slug"]),
         "status": l.get("pipeline_status", "pending"), "score": l.get("lead_score", 0)}
        for l in leads
    ]})


@api_bp.route("/api/leads/<slug>", methods=["PUT"])
def edit_lead(slug):
    """Update lead fields."""
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Only allow updating safe fields
    allowed = {
        "first_name", "last_name", "email", "phone", "company_name",
        "website", "city", "state", "industry", "lead_tier", "lead_score",
        "pipeline_status", "is_qualified", "disqualification_reason",
        "company_description", "employee_count",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        result = db.update_lead(slug, updates)
        if not result:
            return jsonify({"error": "Lead not found"}), 404
        return jsonify({"ok": True, "lead": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

@api_bp.route("/api/emails/compose", methods=["POST"])
def compose_email():
    """Create a standalone email draft (or save & send immediately)."""
    data = request.get_json(silent=True) or {}
    to_email = data.get("to_email", "").strip()
    subject = data.get("subject", "").strip()
    html_content = data.get("html_content", "").strip()
    sender_account = data.get("sender_account", "").strip() or None

    if not to_email or not subject:
        return jsonify({"error": "Recipient and subject are required"}), 400

    # Try to match to an existing lead by email
    lead = db.get_lead_by_email(to_email)

    email_data = {
        "to_email": to_email,
        "subject": subject,
        "html_content": html_content or "",
        "status": "draft",
        "touchpoint": 1,
        "sender_account": sender_account,
        "sent_via": "smtp",
    }
    if lead:
        email_data["lead_id"] = lead["id"]
        email_data["slug"] = lead["slug"]

    email = db.create_email(email_data)
    return jsonify({"ok": True, "email": email})


@api_bp.route("/api/emails/<email_id>/send", methods=["POST"])
def send_email(email_id):
    """Send an email via SMTP."""
    email = db.get_email_by_id(email_id)

    if not email:
        return jsonify({"error": "Email not found"}), 404

    try:
        from services.smtp_sender import send_email_smtp, get_next_sender

        # Determine sender
        sender = email.get("sender_account")
        if not sender:
            acc = get_next_sender()
            sender = acc["email"] if acc else None
        if not sender:
            return jsonify({"error": "No sender account available"}), 400

        # Determine recipient
        lead = db.get_lead_by_id(email.get("lead_id"))
        to_email = email.get("to_email") or (lead.get("email") if lead else "")
        if not to_email:
            return jsonify({"error": "No recipient email address"}), 400

        result = send_email_smtp(
            sender, to_email,
            email.get("subject", ""),
            email.get("html_content", ""),
        )

        if not result["success"]:
            return jsonify({"error": result["error"]}), 500

        # Update email status
        db.update_email(email_id, {
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
            "sender_account": sender,
            "sent_via": "smtp",
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
            message=f"Touch {email.get('touchpoint', 1)} sent via {sender}: {email.get('subject', '')}",
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


@api_bp.route("/api/emails/<email_id>", methods=["PUT"])
def update_email(email_id):
    """Update email subject and/or html_content."""
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No data provided"}), 400

    allowed = {"subject", "html_content", "sender_account"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    try:
        result = db.update_email(email_id, updates)
        if not result:
            return jsonify({"error": "Email not found"}), 404
        return jsonify({"ok": True, "email": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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


# ── Inbox ─────────────────────────────────────────────

@api_bp.route("/api/inbox/messages")
def inbox_messages():
    """Fetch email headers for a tedca.online account."""
    from services.inbox_service import get_tedca_accounts, fetch_inbox
    account_email = request.args.get("account", "")
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 50))

    accounts = get_tedca_accounts()
    account = next((a for a in accounts if a["email"] == account_email), None)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    try:
        messages = fetch_inbox(account, limit=limit, offset=offset)
        return jsonify({"ok": True, "messages": messages, "account": account_email})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/message")
def inbox_message():
    """Fetch full email body by UID."""
    from services.inbox_service import get_tedca_accounts, fetch_message_body
    account_email = request.args.get("account", "")
    uid = request.args.get("uid", "")

    accounts = get_tedca_accounts()
    account = next((a for a in accounts if a["email"] == account_email), None)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    try:
        msg = fetch_message_body(account, uid)
        if not msg:
            return jsonify({"error": "Message not found"}), 404
        return jsonify({"ok": True, "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/mark", methods=["POST"])
def inbox_mark():
    """Mark email read or unread."""
    from services.inbox_service import get_tedca_accounts, mark_message
    data = request.get_json(silent=True) or {}
    account_email = data.get("account", "")
    uid = data.get("uid", "")
    action = data.get("action", "")  # "read" or "unread"

    if action not in ("read", "unread"):
        return jsonify({"error": "action must be 'read' or 'unread'"}), 400

    accounts = get_tedca_accounts()
    account = next((a for a in accounts if a["email"] == account_email), None)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    try:
        mark_message(account, uid, action)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/delete", methods=["POST"])
def inbox_delete():
    """Delete an email."""
    from services.inbox_service import get_tedca_accounts, delete_message
    data = request.get_json(silent=True) or {}
    account_email = data.get("account", "")
    uid = data.get("uid", "")

    accounts = get_tedca_accounts()
    account = next((a for a in accounts if a["email"] == account_email), None)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    try:
        delete_message(account, uid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/auto-replies")
def inbox_auto_replies():
    """List auto-reply records, optionally filtered by status."""
    status = request.args.get("status")
    limit = int(request.args.get("limit", 100))
    try:
        replies = db.get_auto_replies(status=status, limit=limit)
        return jsonify({"ok": True, "auto_replies": replies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/send-draft-reply", methods=["POST"])
def send_draft_reply():
    """Send a previously drafted auto-reply (supports edited body)."""
    from services.auto_reply_service import send_draft_reply as _send_draft
    data = request.get_json(silent=True) or {}
    reply_id = data.get("id", "")
    edited_body = data.get("body")  # Optional: if user edited the draft

    if not reply_id:
        return jsonify({"error": "Missing 'id'"}), 400

    try:
        result = _send_draft(reply_id, edited_body=edited_body)
        if not result:
            return jsonify({"error": "Draft not found or already sent"}), 404
        sse.publish("auto_reply_sent", {
            "id": reply_id,
            "slug": result.get("slug", ""),
            "to": result.get("incoming_from", ""),
        })
        return jsonify({"ok": True, "auto_reply": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/auto-reply-stats")
def auto_reply_stats():
    """Get auto-reply counts by status and sentiment."""
    try:
        stats = db.get_auto_reply_stats()
        return jsonify({"ok": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/inbox/unread-total")
def inbox_unread_total():
    """Get unread counts for all tedca.online accounts."""
    from services.inbox_service import get_unread_counts
    try:
        counts = get_unread_counts()
        total = sum(counts.values())
        return jsonify({"ok": True, "counts": counts, "total": total})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Daily Queue ──────────────────────────────────────

@api_bp.route("/api/queue/today")
def queue_today():
    """Get today's queue with lead + email details."""
    try:
        from services.daily_queue_service import get_todays_queue
        items = get_todays_queue()
        return jsonify({"ok": True, "queue": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/queue/generate", methods=["POST"])
def queue_generate():
    """Manual trigger: generate daily queue."""
    data = request.get_json(silent=True) or {}
    count = min(data.get("count", 6), 20)
    try:
        from services.daily_queue_service import generate_daily_queue
        items = generate_daily_queue(count=count)
        sse.publish("daily_queue_ready", {"count": len(items)})
        return jsonify({"ok": True, "queued": len(items), "items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/queue/send-all", methods=["POST"])
def queue_send_all():
    """Send all queued items in today's queue."""
    try:
        from services.daily_queue_service import approve_and_send_all
        result = approve_and_send_all()
        if result["sent"] > 0:
            sse.publish("queue_sent", {"sent": result["sent"], "failed": result["failed"]})
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/queue/<queue_id>/send", methods=["POST"])
def queue_send_one(queue_id):
    """Send a single queued item."""
    try:
        from services.daily_queue_service import approve_and_send_one
        result = approve_and_send_one(queue_id)
        if result["success"]:
            sse.publish("queue_item_sent", {"queue_id": queue_id})
        return jsonify({"ok": result["success"], **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/queue/<queue_id>/reassign", methods=["POST"])
def queue_reassign(queue_id):
    """Reassign sender for a queue item."""
    data = request.get_json(silent=True) or {}
    new_sender = data.get("sender_account", "")
    if not new_sender:
        return jsonify({"error": "sender_account required"}), 400
    try:
        from services.daily_queue_service import reassign_sender
        item = reassign_sender(queue_id, new_sender)
        return jsonify({"ok": True, "item": item})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/queue/<queue_id>/skip", methods=["POST"])
def queue_skip(queue_id):
    """Skip a queue item."""
    try:
        from services.daily_queue_service import skip_queue_item
        item = skip_queue_item(queue_id)
        return jsonify({"ok": True, "item": item})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Sender Accounts ──────────────────────────────────

@api_bp.route("/api/senders")
def list_senders():
    """List available @tedca.online sender accounts."""
    from services.smtp_sender import get_sender_accounts
    accounts = get_sender_accounts()
    return jsonify({
        "ok": True,
        "senders": [{"email": a["email"], "display_name": a.get("display_name", "")} for a in accounts],
    })
