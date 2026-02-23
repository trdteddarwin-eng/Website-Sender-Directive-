#!/usr/bin/env python3
"""
Supabase CRUD for Upwork application tracking.

-- SQL schema (run once in Supabase SQL editor):
--
-- CREATE TABLE upwork_applications (
--     id SERIAL PRIMARY KEY,
--     job_id TEXT UNIQUE NOT NULL,
--     job_title TEXT,
--     job_url TEXT,
--     job_budget TEXT,
--     job_type TEXT,                        -- 'website' | 'automation' | 'other'
--     relevance_score INTEGER,
--     cover_letter TEXT,
--     bid_amount NUMERIC,
--     deliverable_url TEXT,                 -- Vercel site URL or video URL
--     status TEXT DEFAULT 'pending',        -- pending -> applied -> failed
--     connects_spent INTEGER DEFAULT 0,
--     applied_at TIMESTAMPTZ,
--     error_message TEXT,
--     created_at TIMESTAMPTZ DEFAULT NOW(),
--     updated_at TIMESTAMPTZ DEFAULT NOW()
-- );
--
-- CREATE TABLE upwork_daily_stats (
--     id SERIAL PRIMARY KEY,
--     date DATE UNIQUE NOT NULL,
--     jobs_scraped INTEGER DEFAULT 0,
--     jobs_filtered INTEGER DEFAULT 0,
--     jobs_scored INTEGER DEFAULT 0,
--     jobs_applied INTEGER DEFAULT 0,
--     sites_built INTEGER DEFAULT 0,
--     videos_made INTEGER DEFAULT 0,
--     connects_spent INTEGER DEFAULT 0,
--     errors INTEGER DEFAULT 0,
--     created_at TIMESTAMPTZ DEFAULT NOW()
-- );
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, List
from datetime import datetime, date, timedelta, timezone

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

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def _today() -> str:
    """Return today's date as ISO string (YYYY-MM-DD)."""
    return date.today().isoformat()


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Applications CRUD
# ---------------------------------------------------------------------------

def record_application(
    job_id: str,
    job_title: str,
    job_url: str,
    job_budget: str,
    job_type: str,
    relevance_score: int,
    cover_letter: str,
    bid_amount: Optional[float] = None,
    deliverable_url: Optional[str] = None,
    connects_spent: int = 0,
) -> dict:
    """Insert a new application record. Returns the inserted row."""
    sb = _get_client()
    row = {
        "job_id": job_id,
        "job_title": job_title,
        "job_url": job_url,
        "job_budget": job_budget,
        "job_type": job_type,
        "relevance_score": relevance_score,
        "cover_letter": cover_letter,
        "bid_amount": bid_amount,
        "deliverable_url": deliverable_url,
        "status": "pending",
        "connects_spent": connects_spent,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    resp = sb.table("upwork_applications").insert(row).execute()
    return resp.data[0] if resp.data else {}


def update_application_status(
    job_id: str,
    status: str,
    error_message: Optional[str] = None,
    applied_at: Optional[str] = None,
) -> dict:
    """Update status of an application (pending->applied or pending->failed)."""
    sb = _get_client()
    update = {
        "status": status,
        "updated_at": _now_iso(),
    }
    if error_message is not None:
        update["error_message"] = error_message
    if applied_at is not None:
        update["applied_at"] = applied_at
    elif status == "applied":
        update["applied_at"] = _now_iso()

    resp = (
        sb.table("upwork_applications")
        .update(update)
        .eq("job_id", job_id)
        .execute()
    )
    return resp.data[0] if resp.data else {}


def check_already_applied(job_id: str) -> bool:
    """Check if we've already applied to this job."""
    sb = _get_client()
    resp = (
        sb.table("upwork_applications")
        .select("id")
        .eq("job_id", job_id)
        .execute()
    )
    return len(resp.data) > 0


def check_daily_budget(daily_limit: int = 10, daily_connects_budget: int = 40) -> dict:
    """Check if today's budget allows more applications.

    Returns:
        {
            'can_apply': bool,
            'apps_today': int,
            'connects_today': int,
            'remaining_apps': int,
            'remaining_connects': int,
        }
    """
    stats = get_daily_stats()
    apps = stats.get("jobs_applied", 0)
    connects = stats.get("connects_spent", 0)
    remaining_apps = max(0, daily_limit - apps)
    remaining_connects = max(0, daily_connects_budget - connects)

    return {
        "can_apply": remaining_apps > 0 and remaining_connects > 0,
        "apps_today": apps,
        "connects_today": connects,
        "remaining_apps": remaining_apps,
        "remaining_connects": remaining_connects,
    }


# ---------------------------------------------------------------------------
# Daily Stats
# ---------------------------------------------------------------------------

def get_daily_stats(date_str: Optional[str] = None) -> dict:
    """Get or create daily stats row for given date (default today)."""
    sb = _get_client()
    d = date_str or _today()

    resp = (
        sb.table("upwork_daily_stats")
        .select("*")
        .eq("date", d)
        .execute()
    )
    if resp.data:
        return resp.data[0]

    # Create row for today
    new_row = {
        "date": d,
        "jobs_scraped": 0,
        "jobs_filtered": 0,
        "jobs_scored": 0,
        "jobs_applied": 0,
        "sites_built": 0,
        "videos_made": 0,
        "connects_spent": 0,
        "errors": 0,
    }
    insert_resp = sb.table("upwork_daily_stats").insert(new_row).execute()
    return insert_resp.data[0] if insert_resp.data else new_row


def update_daily_stats(date_str: Optional[str] = None, **kwargs) -> dict:
    """Increment daily stats counters.

    kwargs can include: jobs_scraped, jobs_filtered, jobs_scored,
    jobs_applied, sites_built, videos_made, connects_spent, errors.
    Values are ADDED to current counters (incremental).
    """
    valid_fields = {
        "jobs_scraped", "jobs_filtered", "jobs_scored", "jobs_applied",
        "sites_built", "videos_made", "connects_spent", "errors",
    }
    increments = {k: v for k, v in kwargs.items() if k in valid_fields and v}
    if not increments:
        return get_daily_stats(date_str)

    # Get current values first
    current = get_daily_stats(date_str)
    d = date_str or _today()

    update = {}
    for field, delta in increments.items():
        update[field] = current.get(field, 0) + delta

    sb = _get_client()
    resp = (
        sb.table("upwork_daily_stats")
        .update(update)
        .eq("date", d)
        .execute()
    )
    return resp.data[0] if resp.data else {}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def get_recent_applications(days: int = 7, limit: int = 50) -> List[dict]:
    """Get recent applications for reporting."""
    sb = _get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    resp = (
        sb.table("upwork_applications")
        .select("*")
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Upwork application tracker")
    sub = parser.add_subparsers(dest="command")

    # check-budget
    budget_p = sub.add_parser("check-budget", help="Check daily application budget")
    budget_p.add_argument("--limit", type=int, default=10, help="Daily app limit")
    budget_p.add_argument("--connects", type=int, default=40, help="Daily connects budget")

    # stats
    stats_p = sub.add_parser("stats", help="Get daily stats")
    stats_p.add_argument("--date", type=str, default=None, help="Date (YYYY-MM-DD)")

    # recent
    recent_p = sub.add_parser("recent", help="Get recent applications")
    recent_p.add_argument("--days", type=int, default=7)
    recent_p.add_argument("--limit", type=int, default=50)

    # check-applied
    check_p = sub.add_parser("check-applied", help="Check if already applied to a job")
    check_p.add_argument("job_id", type=str)

    # record (for testing)
    record_p = sub.add_parser("record", help="Record a test application")
    record_p.add_argument("--job-id", required=True)
    record_p.add_argument("--title", required=True)
    record_p.add_argument("--url", default="")
    record_p.add_argument("--budget", default="")
    record_p.add_argument("--type", default="other", choices=["website", "automation", "other"])
    record_p.add_argument("--score", type=int, default=5)
    record_p.add_argument("--letter", default="Test cover letter")

    args = parser.parse_args()

    if args.command == "check-budget":
        result = check_daily_budget(args.limit, args.connects)
        print(json.dumps(result, indent=2))

    elif args.command == "stats":
        result = get_daily_stats(args.date)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "recent":
        result = get_recent_applications(args.days, args.limit)
        print(json.dumps(result, indent=2, default=str))
        print(f"\n{len(result)} applications in the last {args.days} days")

    elif args.command == "check-applied":
        applied = check_already_applied(args.job_id)
        print(f"Already applied: {applied}")

    elif args.command == "record":
        result = record_application(
            job_id=args.job_id,
            job_title=args.title,
            job_url=args.url,
            job_budget=args.budget,
            job_type=args.type,
            relevance_score=args.score,
            cover_letter=args.letter,
        )
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
