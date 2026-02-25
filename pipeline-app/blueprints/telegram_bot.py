"""Telegram webhook blueprint — receives messages from @Tedca_alert_bot."""

import os
import traceback
from flask import Blueprint, request, jsonify

from services.telegram_service import handle_message, handle_callback

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

telegram_bp = Blueprint("telegram_bot", __name__)


@telegram_bp.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json(silent=True)
    if not data:
        return "ok", 200

    # Extract chat_id from either message or callback_query
    chat_id = None
    if "callback_query" in data:
        chat_id = str(data["callback_query"].get("message", {}).get("chat", {}).get("id", ""))
    elif "message" in data:
        chat_id = str(data["message"].get("chat", {}).get("id", ""))

    # Security: only respond to authorized chat
    if TELEGRAM_CHAT_ID and chat_id != TELEGRAM_CHAT_ID:
        return "ok", 200

    try:
        if "callback_query" in data:
            handle_callback(data["callback_query"], chat_id)
        elif "message" in data:
            text = data["message"].get("text", "")
            if text:
                handle_message(text, chat_id)
    except Exception as e:
        print(f"[TelegramBot] ERROR: {e}")
        traceback.print_exc()

    return "ok", 200


@telegram_bp.route("/telegram/test", methods=["GET"])
def telegram_test():
    """Create a test draft on Railway and send notification — full end-to-end test."""
    import uuid
    import requests as req

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    results = {"errors": []}

    # 1. Test Supabase connection
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
        results["supabase_url"] = SUPABASE_URL[:40] + "..." if SUPABASE_URL else "NOT SET"
        results["supabase_key"] = f"set ({len(SUPABASE_KEY)} chars)" if SUPABASE_KEY else "NOT SET"

        from services import supabase_client as test_db
        drafts = test_db.get_auto_replies(status="draft", limit=1)
        results["supabase"] = "ok"
        results["existing_drafts"] = len(drafts)
    except Exception as e:
        import traceback
        results["supabase"] = f"error: {e}"
        results["supabase_traceback"] = traceback.format_exc()[-500:]
        results["errors"].append(f"Supabase failed: {e}")

    # 2. Test Telegram send (plain text, no Markdown)
    try:
        resp = req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "Test: bot is alive."},
            timeout=10,
        )
        results["telegram_send"] = resp.status_code
    except Exception as e:
        results["errors"].append(f"Telegram send error: {e}")

    # 3. If Supabase works, load the latest draft into active state
    if results.get("supabase") == "ok" and results.get("existing_drafts", 0) > 0:
        try:
            from services.telegram_service import _load_active_draft, _send_status
            draft = _load_active_draft()
            if draft:
                results["active_draft_set"] = True
                results["draft_id"] = draft.get("auto_reply_id", "")[:8]
                # Send status message to Telegram so user sees the draft
                _send_status(chat_id)
                results["status_sent"] = True
            else:
                results["active_draft_set"] = False
        except Exception as e:
            results["errors"].append(f"Draft load/send failed: {e}")

    return jsonify(results)
