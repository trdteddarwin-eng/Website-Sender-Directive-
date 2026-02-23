#!/usr/bin/env python3
"""
Upwork browser session (cookie) persistence via Supabase.

-- SQL schema (run once in Supabase SQL editor):
--
-- CREATE TABLE upwork_sessions (
--   id serial PRIMARY KEY,
--   session_name text UNIQUE DEFAULT 'default',
--   cookies jsonb NOT NULL,
--   user_agent text,
--   viewport jsonb DEFAULT '{"width": 1920, "height": 1080}',
--   last_verified timestamptz,
--   is_valid boolean DEFAULT true,
--   created_at timestamptz DEFAULT now(),
--   updated_at timestamptz DEFAULT now()
-- );
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

TABLE = "upwork_sessions"

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_session(
    cookies: list[dict],
    user_agent: str = None,
    session_name: str = "default",
) -> bool:
    """Save browser cookies to Supabase.

    Upserts on session_name so repeated saves overwrite the previous session.
    Returns True on success.
    """
    sb = _get_client()
    row = {
        "session_name": session_name,
        "cookies": cookies,
        "is_valid": True,
        "updated_at": _now_iso(),
        "last_verified": _now_iso(),
    }
    if user_agent:
        row["user_agent"] = user_agent

    try:
        resp = (
            sb.table(TABLE)
            .upsert(row, on_conflict="session_name")
            .execute()
        )
        return bool(resp.data)
    except Exception as e:
        print(f"[session_manager] Error saving session: {e}")
        return False


def load_session(session_name: str = "default") -> Optional[dict]:
    """Load session from Supabase.

    Returns:
        {
            'cookies': [...],
            'user_agent': str,
            'viewport': {'width': int, 'height': int},
        }
        or None if no valid session exists.
    """
    sb = _get_client()
    try:
        resp = (
            sb.table(TABLE)
            .select("cookies, user_agent, viewport, is_valid")
            .eq("session_name", session_name)
            .execute()
        )
        if not resp.data:
            return None

        row = resp.data[0]
        if not row.get("is_valid", False):
            print(f"[session_manager] Session '{session_name}' exists but is marked invalid.")
            return None

        cookies = row.get("cookies", [])
        # Handle case where cookies are stored as a JSON string
        if isinstance(cookies, str):
            cookies = json.loads(cookies)

        viewport = row.get("viewport", {"width": 1920, "height": 1080})
        if isinstance(viewport, str):
            viewport = json.loads(viewport)

        return {
            "cookies": cookies,
            "user_agent": row.get("user_agent"),
            "viewport": viewport,
        }
    except Exception as e:
        print(f"[session_manager] Error loading session: {e}")
        return None


def check_session_health(page, session_name: str = "default") -> bool:
    """Navigate to /nx/find-work/ and verify we are not redirected to login.

    Updates last_verified and is_valid in DB.
    Returns True if the session is still valid.
    """
    try:
        response = page.goto(
            "https://www.upwork.com/nx/find-work/",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # Wait a moment for any redirects to settle
        page.wait_for_timeout(3000)

        current_url = page.url
        is_valid = "/login" not in current_url and "/account-security" not in current_url

        # Update DB
        _update_session_fields(session_name, {
            "last_verified": _now_iso(),
            "is_valid": is_valid,
            "updated_at": _now_iso(),
        })

        if not is_valid:
            print(f"[session_manager] Session '{session_name}' is INVALID (redirected to: {current_url})")
        else:
            print(f"[session_manager] Session '{session_name}' is valid.")

        return is_valid
    except Exception as e:
        print(f"[session_manager] Error checking session health: {e}")
        _update_session_fields(session_name, {
            "is_valid": False,
            "updated_at": _now_iso(),
        })
        return False


def invalidate_session(session_name: str = "default") -> bool:
    """Mark session as invalid in DB."""
    return _update_session_fields(session_name, {
        "is_valid": False,
        "updated_at": _now_iso(),
    })


def update_session(session_name: str = "default", **kwargs) -> bool:
    """Update session fields (cookies, user_agent, viewport, etc.).

    Example:
        update_session("default", cookies=[...], user_agent="Mozilla/5.0 ...")
    """
    allowed_fields = {"cookies", "user_agent", "viewport", "is_valid", "last_verified"}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not update_data:
        print("[session_manager] No valid fields to update.")
        return False

    update_data["updated_at"] = _now_iso()
    return _update_session_fields(session_name, update_data)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _update_session_fields(session_name: str, fields: dict) -> bool:
    """Update arbitrary fields on a session row."""
    sb = _get_client()
    try:
        resp = (
            sb.table(TABLE)
            .update(fields)
            .eq("session_name", session_name)
            .execute()
        )
        return bool(resp.data)
    except Exception as e:
        print(f"[session_manager] Error updating session: {e}")
        return False
