"""Settings blueprint — GET /settings."""

import os
from flask import Blueprint, render_template
from config import SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY, NETLIFY_AUTH_TOKEN, ANTHROPIC_API_KEY

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

    supabase_configured = bool(SUPABASE_URL and SUPABASE_KEY and "YOUR_" not in SUPABASE_URL)
    supabase_lead_count = 0
    if supabase_configured:
        try:
            from services import supabase_client as db
            counts = db.get_lead_counts()
            supabase_lead_count = counts.get("total", 0)
        except Exception:
            pass

    keys = {
        "SUPABASE_URL": mask(SUPABASE_URL) if SUPABASE_URL else "(not set)",
        "SUPABASE_KEY": mask(SUPABASE_KEY) if SUPABASE_KEY else "(not set)",
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
                           supabase_configured=supabase_configured,
                           supabase_lead_count=supabase_lead_count)
