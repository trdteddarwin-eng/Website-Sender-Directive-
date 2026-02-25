"""Telegram bot service — handles draft revision, send/skip commands."""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "execution"))

from services import supabase_client as db
from services.auto_reply_service import send_draft_reply

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# In-memory state: one user, one active draft at a time
_active_draft = {}


def _send_telegram(text, chat_id=None, reply_markup=None):
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return
    payload = {
        "chat_id": chat_id or TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print(f"[TelegramService] Send failed: {e}")


def _answer_callback(callback_query_id, text=""):
    """Acknowledge an inline button press."""
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def set_active_draft(auto_reply_id, reply_body, reply_subject, lead_name,
                     company, sender_name, incoming_from):
    """Called by _notify_telegram when a new draft is created."""
    global _active_draft
    _active_draft = {
        "auto_reply_id": auto_reply_id,
        "current_body": reply_body,
        "reply_subject": reply_subject,
        "lead_name": lead_name,
        "company": company,
        "sender_name": sender_name,
        "incoming_from": incoming_from,
    }


def get_active_draft():
    """Return current active draft (for testing/debugging)."""
    return _active_draft


def handle_message(text, chat_id):
    """Route incoming Telegram text messages."""
    text_lower = text.strip().lower()

    if text_lower in ("send", "approve", "yes", "go"):
        return _send_current_draft(chat_id)
    elif text_lower in ("skip", "discard", "no", "cancel"):
        return _skip_current_draft(chat_id)
    elif text_lower in ("status", "hello", "hi"):
        return _send_status(chat_id)
    else:
        return _revise_current_draft(text, chat_id)


def handle_callback(callback_query, chat_id):
    """Handle inline button presses (send_<id> or skip_<id>)."""
    callback_data = callback_query.get("data", "")
    callback_id = callback_query.get("id", "")

    if callback_data.startswith("send_"):
        auto_reply_id = callback_data[5:]
        _answer_callback(callback_id, "Sending...")
        return _send_draft_by_id(auto_reply_id, chat_id)
    elif callback_data.startswith("skip_"):
        auto_reply_id = callback_data[5:]
        _answer_callback(callback_id, "Skipped")
        return _skip_draft_by_id(auto_reply_id, chat_id)
    else:
        _answer_callback(callback_id, "Unknown action")


def _send_current_draft(chat_id):
    """Send the currently active draft."""
    global _active_draft
    if not _active_draft:
        _send_telegram("No active draft to send. Wait for a new lead reply.", chat_id)
        return

    return _send_draft_by_id(_active_draft["auto_reply_id"], chat_id)


def _send_draft_by_id(auto_reply_id, chat_id):
    """Send a specific draft by its auto_reply_id."""
    global _active_draft
    try:
        result = send_draft_reply(
            auto_reply_id,
            edited_body=_active_draft.get("current_body") if _active_draft.get("auto_reply_id") == auto_reply_id else None,
        )
        if result:
            to_email = result.get("incoming_from", "unknown")
            _send_telegram(f"Sent to {to_email}", chat_id)
            if _active_draft.get("auto_reply_id") == auto_reply_id:
                _active_draft = {}
        else:
            _send_telegram("Failed to send — draft may already be sent or missing.", chat_id)
    except Exception as e:
        _send_telegram(f"Send failed: {e}", chat_id)


def _skip_current_draft(chat_id):
    """Skip/discard the currently active draft."""
    global _active_draft
    if not _active_draft:
        _send_telegram("No active draft to skip.", chat_id)
        return

    return _skip_draft_by_id(_active_draft["auto_reply_id"], chat_id)


def _skip_draft_by_id(auto_reply_id, chat_id):
    """Skip a specific draft by its auto_reply_id."""
    global _active_draft
    try:
        db.update_auto_reply(auto_reply_id, {"status": "skipped"})
        _send_telegram("Draft discarded.", chat_id)
        if _active_draft.get("auto_reply_id") == auto_reply_id:
            _active_draft = {}
    except Exception as e:
        _send_telegram(f"Skip failed: {e}", chat_id)


def _revise_current_draft(feedback, chat_id):
    """Revise the active draft using AI based on user feedback."""
    global _active_draft
    if not _active_draft:
        _send_telegram(
            "No active draft to revise. Wait for a new lead reply, or type \"status\" to check.",
            chat_id,
        )
        return

    _send_telegram("Revising draft...", chat_id)

    try:
        from generate_reply_email import revise_reply

        result = revise_reply(
            current_draft=_active_draft["current_body"],
            user_feedback=feedback,
            lead_name=_active_draft["lead_name"],
            company=_active_draft["company"],
            sender_name=_active_draft["sender_name"],
        )

        new_body = result.get("reply_body", _active_draft["current_body"])
        _active_draft["current_body"] = new_body

        # Update in Supabase too
        db.update_auto_reply(_active_draft["auto_reply_id"], {"reply_body": new_body})

        # Show revised draft
        msg = (
            f"*Revised draft:*\n"
            f"---\n{new_body}\n---\n\n"
            f"Reply to revise again • \"send\" to approve • \"skip\" to discard"
        )
        _send_telegram(msg, chat_id)

    except Exception as e:
        _send_telegram(f"Revision failed: {e}", chat_id)


def _send_status(chat_id):
    """Send bot status / active draft info."""
    if _active_draft:
        lead = _active_draft.get("lead_name", "Unknown")
        company = _active_draft.get("company", "")
        msg = (
            f"*Active draft:*\n"
            f"To: {lead} ({company})\n\n"
            f"---\n{_active_draft['current_body']}\n---\n\n"
            f"Reply to revise • \"send\" to approve • \"skip\" to discard"
        )
    else:
        msg = "No active draft. I'll notify you when a lead replies."
    _send_telegram(msg, chat_id)
