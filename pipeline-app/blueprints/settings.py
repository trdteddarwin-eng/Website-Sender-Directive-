"""Settings blueprint — GET /settings."""

import os
from flask import Blueprint, render_template
from config import GOOGLE_SHEET_URL, GOOGLE_TOKEN_PATH, OPENROUTER_API_KEY, NETLIFY_AUTH_TOKEN, ANTHROPIC_API_KEY

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings_page():
    # Mask API keys for display
    def mask(key):
        if not key:
            return ""
        if len(key) <= 8:
            return "***"
        return key[:4] + "..." + key[-4:]

    sheets_configured = os.path.exists(GOOGLE_TOKEN_PATH)
    sheets_lead_count = 0
    if sheets_configured:
        try:
            from services import supabase_client as db
            counts = db.get_lead_counts()
            sheets_lead_count = counts.get("total", 0)
        except Exception:
            pass

    keys = {
        "GOOGLE_SHEET": GOOGLE_SHEET_URL[:60] + "..." if GOOGLE_SHEET_URL else "(not set)",
        "OPENROUTER_API_KEY": mask(OPENROUTER_API_KEY),
        "NETLIFY_AUTH_TOKEN": mask(NETLIFY_AUTH_TOKEN),
        "ANTHROPIC_API_KEY": mask(ANTHROPIC_API_KEY),
    }

    gmail_ok = False
    gmail_email = ""
    try:
        from services.email_service import check_gmail_auth
        result = check_gmail_auth()
        gmail_ok = result.get("ok", False)
        gmail_email = result.get("email", "")
    except Exception:
        pass

    return render_template("settings.html",
                           keys=keys,
                           gmail_ok=gmail_ok,
                           gmail_email=gmail_email,
                           sheets_configured=sheets_configured,
                           sheets_lead_count=sheets_lead_count)
