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
    """Send a test message through the full handler flow and return diagnostics."""
    from services.telegram_service import _load_active_draft

    errors = []
    results = {}

    # 1. Check if draft loads from Supabase
    try:
        draft = _load_active_draft()
        if draft:
            results["draft_loaded"] = True
            results["draft_id"] = draft.get("auto_reply_id", "")[:8]
            results["lead_name"] = draft.get("lead_name", "")
            results["body_preview"] = draft.get("current_body", "")[:80]
        else:
            results["draft_loaded"] = False
            errors.append("No draft found in Supabase with status=draft")
    except Exception as e:
        results["draft_loaded"] = False
        errors.append(f"Draft load error: {e}")

    # 2. Try sending a plain text message (no Markdown)
    import requests as req
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    try:
        resp = req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "Test: bot is alive and can send messages."},
            timeout=10,
        )
        results["plain_send"] = f"{resp.status_code}"
        if not resp.ok:
            errors.append(f"Plain send failed: {resp.text[:200]}")
    except Exception as e:
        errors.append(f"Plain send error: {e}")

    # 3. Try sending WITH Markdown (like the handler does)
    if draft:
        test_msg = (
            f"*Active draft:*\n"
            f"To: {draft.get('lead_name', 'test')} ({draft.get('company', 'test')})\n\n"
            f"---\n{draft.get('current_body', 'test body')}\n---\n\n"
            f"Reply to revise"
        )
        try:
            resp2 = req.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": test_msg, "parse_mode": "Markdown"},
                timeout=10,
            )
            results["markdown_send"] = f"{resp2.status_code}"
            if not resp2.ok:
                errors.append(f"Markdown send failed: {resp2.text[:300]}")
        except Exception as e:
            errors.append(f"Markdown send error: {e}")

    results["errors"] = errors
    return jsonify(results)
