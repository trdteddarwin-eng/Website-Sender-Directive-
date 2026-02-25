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
        print(f"[TelegramBot] Rejected message from chat_id={chat_id} (expected {TELEGRAM_CHAT_ID})")
        return "ok", 200

    try:
        if "callback_query" in data:
            handle_callback(data["callback_query"], chat_id)
        elif "message" in data:
            text = data["message"].get("text", "")
            if text:
                print(f"[TelegramBot] Received: '{text}' from chat_id={chat_id}")
                handle_message(text, chat_id)
    except Exception as e:
        print(f"[TelegramBot] ERROR handling message: {e}")
        traceback.print_exc()

    return "ok", 200


@telegram_bp.route("/telegram/debug", methods=["GET"])
def telegram_debug():
    """Debug endpoint — shows env var status and tests sending a message."""
    import requests as req

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    openrouter = os.getenv("OPENROUTER_API_KEY", "")

    # Strip whitespace (Railway env vars sometimes have trailing chars)
    token = token.strip()
    chat_id = chat_id.strip()

    # Try sending a test message
    send_result = "skipped"
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = req.post(
                url,
                json={"chat_id": chat_id, "text": "Debug test from Railway"},
                timeout=10,
            )
            send_result = f"{resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            send_result = f"error: {e}"

    return jsonify({
        "TELEGRAM_BOT_TOKEN": f"set ({len(token)} chars)" if token else "NOT SET",
        "TELEGRAM_CHAT_ID": chat_id if chat_id else "NOT SET",
        "OPENROUTER_API_KEY": f"set ({len(openrouter)} chars)" if openrouter else "NOT SET",
        "RAILWAY_PUBLIC_DOMAIN": os.getenv("RAILWAY_PUBLIC_DOMAIN", "NOT SET"),
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT SET"),
        "test_send_result": send_result,
    })
