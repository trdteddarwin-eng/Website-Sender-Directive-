"""Telegram webhook blueprint — receives messages from @Tedca_alert_bot."""

import os
from flask import Blueprint, request

from services.telegram_service import handle_message, handle_callback

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

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

    if "callback_query" in data:
        handle_callback(data["callback_query"], chat_id)
    elif "message" in data:
        text = data["message"].get("text", "")
        if text:
            handle_message(text, chat_id)

    return "ok", 200
