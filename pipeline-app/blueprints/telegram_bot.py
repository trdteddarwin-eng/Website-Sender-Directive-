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
    """Test the full flow: load draft from Supabase, send message to Telegram."""
    import requests as req

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    results = {"errors": []}

    # 1. Test draft loading
    try:
        from services.telegram_service import _load_active_draft
        draft = _load_active_draft()
        if draft:
            results["draft"] = {
                "id": draft.get("auto_reply_id", "")[:8],
                "lead": draft.get("lead_name", ""),
                "body_preview": draft.get("current_body", "")[:80],
            }
        else:
            results["draft"] = None
            results["errors"].append("No draft with status=draft found in Supabase")
    except Exception as e:
        results["draft"] = None
        results["errors"].append(f"Draft load failed: {e}")

    # 2. Send plain text test
    try:
        resp = req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "Test: bot can send plain text."},
            timeout=10,
        )
        results["plain_text_send"] = resp.status_code
        if not resp.ok:
            results["errors"].append(f"Plain text failed: {resp.text[:200]}")
    except Exception as e:
        results["errors"].append(f"Send error: {e}")

    # 3. Send a message with draft content (like the handler does)
    if results.get("draft"):
        body = results["draft"]["body_preview"]
        lead = results["draft"]["lead"]
        msg = f"Active draft:\nTo: {lead}\n\n---\n{body}\n---\n\nReply to revise, \"send\" to approve, \"skip\" to discard"
        try:
            resp2 = req.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg},
                timeout=10,
            )
            results["draft_send"] = resp2.status_code
            if not resp2.ok:
                results["errors"].append(f"Draft send failed: {resp2.text[:200]}")
        except Exception as e:
            results["errors"].append(f"Draft send error: {e}")

    return jsonify(results)
