"""Data layer — Supabase (Postgres) for all persistent data."""

import os
import sys
import re
import json
import uuid
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SUPABASE_URL, SUPABASE_KEY

# ── Supabase Client (lazy init) ──────────────────────

_client = None


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Helpers ───────────────────────────────────────────

def _slugify(company_name):
    if not company_name:
        return ""
    name = str(company_name).split(",")[0].strip()
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _make_id(slug):
    """Deterministic UUID from slug so IDs are stable."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lead.{slug}"))


def _add_lead_aliases(lead):
    """Add template-friendly aliases (tier, status) to a lead dict."""
    if lead:
        lead["tier"] = lead.get("lead_tier", "")
        lead["status"] = lead.get("pipeline_status", "pending")
    return lead


def _ser(obj):
    """JSON serializer for dates."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _clean_for_insert(data, strip_keys=None):
    """Remove None-valued keys and specified keys before inserting."""
    strip_keys = strip_keys or set()
    cleaned = {}
    for k, v in data.items():
        if k in strip_keys:
            continue
        if isinstance(v, (datetime, date)):
            cleaned[k] = v.isoformat()
        elif isinstance(v, dict):
            cleaned[k] = json.dumps(v) if not isinstance(v, str) else v
        else:
            cleaned[k] = v
    return cleaned


# ── Leads ─────────────────────────────────────────────

def get_leads(tier=None, status=None, search=None, sort_by="lead_score",
              sort_dir="desc", page=1, per_page=50):
    """Fetch leads with optional filters, search, sorting, pagination."""
    sb = _get_client()
    query = sb.table("leads").select("*", count="exact")

    if tier:
        query = query.eq("lead_tier", tier)
    if status:
        query = query.eq("pipeline_status", status)
    if search:
        # ilike search across company_name, first_name, last_name, city
        s = f"%{search}%"
        query = query.or_(
            f"company_name.ilike.{s},"
            f"first_name.ilike.{s},"
            f"last_name.ilike.{s},"
            f"city.ilike.{s}"
        )

    # Sort
    desc = sort_dir == "desc"
    query = query.order(sort_by, desc=desc)

    # Pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()
    leads = [_add_lead_aliases(r) for r in (result.data or [])]
    total = result.count if result.count is not None else len(leads)
    return leads, total


def get_lead_by_slug(slug):
    sb = _get_client()
    result = sb.table("leads").select("*").eq("slug", slug).limit(1).execute()
    if result.data:
        return _add_lead_aliases(result.data[0])
    return None


def get_lead_by_id(lead_id):
    sb = _get_client()
    result = sb.table("leads").select("*").eq("id", lead_id).limit(1).execute()
    if result.data:
        return _add_lead_aliases(result.data[0])
    return None


def get_lead_by_email(email):
    """Look up a lead by email address."""
    sb = _get_client()
    result = sb.table("leads").select("*").eq("email", email).limit(1).execute()
    if result.data:
        return _add_lead_aliases(result.data[0])
    return None


def upsert_lead(data):
    """Insert or update a lead by slug."""
    sb = _get_client()
    slug = data.get("slug", "")
    if not slug:
        return None

    # Ensure deterministic ID
    if "id" not in data:
        data["id"] = _make_id(slug)

    # Convert score_breakdown dict to JSON string if needed
    if "score_breakdown" in data and isinstance(data["score_breakdown"], dict):
        data["score_breakdown"] = json.dumps(data["score_breakdown"])

    # Convert raw_data dict to JSON string if needed
    if "raw_data" in data and isinstance(data["raw_data"], dict):
        data["raw_data"] = json.dumps(data["raw_data"])

    data["updated_at"] = datetime.utcnow().isoformat()

    result = sb.table("leads").upsert(data, on_conflict="slug").execute()
    if result.data:
        return _add_lead_aliases(result.data[0])
    return get_lead_by_slug(slug)


def update_lead(slug, updates):
    """Update specific fields for a lead."""
    sb = _get_client()
    updates["updated_at"] = datetime.utcnow().isoformat()
    result = sb.table("leads").update(updates).eq("slug", slug).execute()
    if result.data:
        return _add_lead_aliases(result.data[0])
    return None


def get_next_unprocessed_lead():
    """Get the highest-scored HOT lead that hasn't been processed yet."""
    sb = _get_client()
    result = (
        sb.table("leads")
        .select("*")
        .eq("lead_tier", "hot")
        .eq("pipeline_status", "pending")
        .eq("is_qualified", True)
        .order("lead_score", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return _add_lead_aliases(result.data[0])
    return None


def get_lead_counts():
    """Get counts by tier and status for dashboard KPIs."""
    sb = _get_client()
    result = sb.table("leads").select("lead_tier,pipeline_status").execute()
    rows = result.data or []
    total = len(rows)
    return {
        "total": total,
        "hot": sum(1 for r in rows if r.get("lead_tier") == "hot"),
        "warm": sum(1 for r in rows if r.get("lead_tier") == "warm"),
        "cold": sum(1 for r in rows if r.get("lead_tier") not in ("hot", "warm") and r.get("lead_tier")),
        "pending": sum(1 for r in rows if r.get("pipeline_status") == "pending"),
        "completed": sum(1 for r in rows if r.get("pipeline_status") == "completed"),
        "processing": sum(1 for r in rows if r.get("pipeline_status") not in ("pending", "completed", "failed")),
        "failed": sum(1 for r in rows if r.get("pipeline_status") == "failed"),
    }


# ── Pipeline Runs ────────────────────────────────────

def create_pipeline_run(lead_id, slug, palette_index, hero_style_index):
    sb = _get_client()
    data = {
        "lead_id": lead_id,
        "slug": slug,
        "status": "running",
        "palette_index": palette_index,
        "hero_style_index": hero_style_index,
        "started_at": datetime.utcnow().isoformat(),
        "agents": json.dumps({
            "researcher": {"status": "waiting", "task": "", "completed_tasks": []},
            "designer": {"status": "waiting", "task": "", "completed_tasks": []},
            "judge": {"status": "waiting", "task": "", "completed_tasks": []},
            "ops": {"status": "waiting", "task": "", "completed_tasks": []},
        }),
        "log": json.dumps([]),
    }
    result = sb.table("pipeline_runs").insert(data).execute()
    return result.data[0] if result.data else data


def _parse_run_json(run):
    """Parse JSON string fields in a pipeline run record."""
    if not run:
        return run
    for key in ("agents", "log"):
        val = run.get(key)
        if isinstance(val, str):
            try:
                run[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
    return run


def get_pipeline_run(run_id):
    sb = _get_client()
    result = sb.table("pipeline_runs").select("*").eq("id", run_id).limit(1).execute()
    return _parse_run_json(result.data[0]) if result.data else None


def get_active_pipeline_run():
    sb = _get_client()
    result = (
        sb.table("pipeline_runs")
        .select("*")
        .eq("status", "running")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )
    return _parse_run_json(result.data[0]) if result.data else None


def update_pipeline_run(run_id, updates):
    sb = _get_client()
    # Serialize JSONB fields
    if "agents" in updates and isinstance(updates["agents"], dict):
        updates["agents"] = json.dumps(updates["agents"])
    if "log" in updates and isinstance(updates["log"], list):
        updates["log"] = json.dumps(updates["log"])
    result = sb.table("pipeline_runs").update(updates).eq("id", run_id).execute()
    return result.data[0] if result.data else None


def get_recent_pipeline_runs(limit=10):
    sb = _get_client()
    result = (
        sb.table("pipeline_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [_parse_run_json(r) for r in (result.data or [])]


# ── Spec Sites ───────────────────────────────────────

def create_spec_site(data):
    sb = _get_client()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "deployed_at" not in data:
        data["deployed_at"] = datetime.utcnow().isoformat()
    result = sb.table("spec_sites").insert(data).execute()
    return result.data[0] if result.data else data


def get_spec_site_by_lead(lead_id):
    sb = _get_client()
    result = (
        sb.table("spec_sites")
        .select("*")
        .eq("lead_id", lead_id)
        .order("deployed_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Emails ───────────────────────────────────────────

def create_email(data):
    sb = _get_client()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "created_at" not in data:
        data["created_at"] = datetime.utcnow().isoformat()
    # Serialize attachments if dict/list
    if "attachments" in data and isinstance(data["attachments"], (list, dict)):
        data["attachments"] = json.dumps(data["attachments"])
    result = sb.table("emails").insert(data).execute()
    return result.data[0] if result.data else data


def get_emails_for_lead(lead_id):
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("*")
        .eq("lead_id", lead_id)
        .order("touchpoint")
        .execute()
    )
    return result.data or []


def update_email(email_id, updates):
    sb = _get_client()
    result = sb.table("emails").update(updates).eq("id", email_id).execute()
    return result.data[0] if result.data else None


def get_emails_by_status(status, limit=50):
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("*")
        .eq("status", status)
        .order("scheduled_send_date")
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_email_by_id(email_id):
    sb = _get_client()
    result = sb.table("emails").select("*").eq("id", email_id).limit(1).execute()
    return result.data[0] if result.data else None


def get_emails_by_lead_and_statuses(lead_id, statuses):
    """Get emails for a lead filtered by a list of statuses."""
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("*")
        .eq("lead_id", lead_id)
        .in_("status", statuses)
        .order("touchpoint")
        .execute()
    )
    return result.data or []


def get_email_stats():
    sb = _get_client()
    result = sb.table("emails").select("status,open_count").execute()
    rows = result.data or []
    total = len(rows)
    sent = sum(1 for e in rows if e.get("status") in ("sent", "opened", "replied"))
    opened = sum(1 for e in rows if e.get("status") in ("opened", "replied") or (e.get("open_count") or 0) > 0)
    replied = sum(1 for e in rows if e.get("status") == "replied")
    bounced = sum(1 for e in rows if e.get("status") == "bounced")
    return {
        "total": total,
        "sent": sent,
        "opened": opened,
        "replied": replied,
        "bounced": bounced,
        "open_rate": round(opened / sent * 100, 1) if sent else 0,
        "reply_rate": round(replied / sent * 100, 1) if sent else 0,
        "bounce_rate": round(bounced / sent * 100, 1) if sent else 0,
    }


# ── Email Sequences ──────────────────────────────────

def create_sequence(data):
    sb = _get_client()
    slug = data.get("slug", "")
    if slug:
        existing = get_sequence_by_slug(slug)
        if existing:
            sb.table("email_sequences").update(data).eq("id", existing["id"]).execute()
            return {**existing, **data}
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "started_at" not in data:
        data["started_at"] = datetime.utcnow().isoformat()
    result = sb.table("email_sequences").insert(data).execute()
    return result.data[0] if result.data else data


def get_sequence_by_slug(slug):
    sb = _get_client()
    result = sb.table("email_sequences").select("*").eq("slug", slug).limit(1).execute()
    return result.data[0] if result.data else None


def get_active_sequences():
    sb = _get_client()
    result = (
        sb.table("email_sequences")
        .select("*")
        .eq("status", "active")
        .order("next_send_date")
        .execute()
    )
    return result.data or []


def get_due_sequences(today=None):
    if today is None:
        today = date.today().isoformat()
    sb = _get_client()
    result = (
        sb.table("email_sequences")
        .select("*")
        .eq("status", "active")
        .lte("next_send_date", today)
        .order("next_send_date")
        .execute()
    )
    return result.data or []


def update_sequence(seq_id, updates):
    sb = _get_client()
    result = sb.table("email_sequences").update(updates).eq("id", seq_id).execute()
    return result.data[0] if result.data else None


def get_all_sequences(status=None, limit=100):
    sb = _get_client()
    query = sb.table("email_sequences").select("*")
    if status:
        query = query.eq("status", status)
    query = query.order("started_at", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


# ── Replies ──────────────────────────────────────────

def create_reply(data):
    sb = _get_client()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "detected_at" not in data:
        data["detected_at"] = datetime.utcnow().isoformat()
    result = sb.table("replies").insert(data).execute()
    return result.data[0] if result.data else data


def get_replies_for_lead(lead_id):
    sb = _get_client()
    result = (
        sb.table("replies")
        .select("*")
        .eq("lead_id", lead_id)
        .order("received_at", desc=True)
        .execute()
    )
    return result.data or []


def get_reply_stats():
    sb = _get_client()
    result = sb.table("replies").select("sentiment").execute()
    rows = result.data or []
    return {
        "total": len(rows),
        "positive": sum(1 for r in rows if r.get("sentiment") == "positive"),
        "negative": sum(1 for r in rows if r.get("sentiment") == "negative"),
        "neutral": sum(1 for r in rows if r.get("sentiment") == "neutral"),
        "out_of_office": sum(1 for r in rows if r.get("sentiment") == "out_of_office"),
    }


# ── Auto Replies ─────────────────────────────────────

def create_auto_reply(data):
    sb = _get_client()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "created_at" not in data:
        data["created_at"] = datetime.utcnow().isoformat()
    result = sb.table("auto_replies").insert(data).execute()
    return result.data[0] if result.data else data


def get_auto_reply_by_uid(uid):
    sb = _get_client()
    result = sb.table("auto_replies").select("*").eq("incoming_uid", uid).limit(1).execute()
    return result.data[0] if result.data else None


def get_auto_reply_by_id(reply_id):
    sb = _get_client()
    result = sb.table("auto_replies").select("*").eq("id", reply_id).limit(1).execute()
    return result.data[0] if result.data else None


def get_auto_replies(status=None, limit=100):
    sb = _get_client()
    query = sb.table("auto_replies").select("*")
    if status:
        query = query.eq("status", status)
    query = query.order("created_at", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


def update_auto_reply(reply_id, updates):
    sb = _get_client()
    result = sb.table("auto_replies").update(updates).eq("id", reply_id).execute()
    return result.data[0] if result.data else None


def get_auto_reply_stats():
    sb = _get_client()
    result = sb.table("auto_replies").select("status,sentiment").execute()
    rows = result.data or []
    return {
        "total": len(rows),
        "sent": sum(1 for r in rows if r.get("status") == "sent"),
        "draft": sum(1 for r in rows if r.get("status") == "draft"),
        "failed": sum(1 for r in rows if r.get("status") == "failed"),
        "skipped_ooo": sum(1 for r in rows if r.get("status") == "skipped_ooo"),
        "positive": sum(1 for r in rows if r.get("sentiment") == "positive"),
        "negative": sum(1 for r in rows if r.get("sentiment") == "negative"),
        "neutral": sum(1 for r in rows if r.get("sentiment") == "neutral"),
        "out_of_office": sum(1 for r in rows if r.get("sentiment") == "out_of_office"),
    }


# ── Activity Log ─────────────────────────────────────

def log_activity(lead_id=None, slug=None, event_type="", event_data=None,
                 agent=None, message=None):
    sb = _get_client()
    data = {
        "lead_id": lead_id,
        "slug": slug,
        "event_type": event_type,
        "event_data": json.dumps(event_data or {}),
        "agent": agent,
        "message": message,
    }
    result = sb.table("activity_log").insert(data).execute()
    return result.data[0] if result.data else data


def get_recent_activity(limit=50, lead_id=None):
    sb = _get_client()
    query = sb.table("activity_log").select("*")
    if lead_id:
        query = query.eq("lead_id", lead_id)
    query = query.order("created_at", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


def get_activity_for_slug(slug, limit=100):
    sb = _get_client()
    result = (
        sb.table("activity_log")
        .select("*")
        .eq("slug", slug)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


# ── Daily Queue ──────────────────────────────────────

def create_queue_item(data):
    sb = _get_client()
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    if "created_at" not in data:
        data["created_at"] = datetime.utcnow().isoformat()
    result = sb.table("daily_queue").insert(data).execute()
    return result.data[0] if result.data else data


def get_todays_queue():
    sb = _get_client()
    today = date.today().isoformat()
    result = (
        sb.table("daily_queue")
        .select("*")
        .eq("queue_date", today)
        .order("created_at")
        .execute()
    )
    return result.data or []


def get_queue_item(queue_id):
    sb = _get_client()
    result = sb.table("daily_queue").select("*").eq("id", queue_id).limit(1).execute()
    return result.data[0] if result.data else None


def update_queue_item(queue_id, updates):
    sb = _get_client()
    result = sb.table("daily_queue").update(updates).eq("id", queue_id).execute()
    return result.data[0] if result.data else None


def get_queue_stats(days=30):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sb = _get_client()
    result = (
        sb.table("daily_queue")
        .select("status,queue_date")
        .gte("created_at", cutoff)
        .execute()
    )
    rows = result.data or []
    return {
        "total": len(rows),
        "sent": sum(1 for r in rows if r.get("status") == "sent"),
        "skipped": sum(1 for r in rows if r.get("status") == "skipped"),
        "queued": sum(1 for r in rows if r.get("status") == "queued"),
    }


# ── Enhanced Email Queries ───────────────────────────

def get_draft_emails(limit=100):
    """All emails with status='draft'."""
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("*")
        .eq("status", "draft")
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_sends_per_sender_today(today=None):
    """Count emails sent per sender_account for a given date."""
    if today is None:
        today = date.today().isoformat()
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("sender_account")
        .eq("status", "sent")
        .gte("sent_at", today + "T00:00:00")
        .lte("sent_at", today + "T23:59:59")
        .execute()
    )
    counts = {}
    for row in (result.data or []):
        acc = row.get("sender_account") or ""
        if acc:
            counts[acc] = counts.get(acc, 0) + 1
    return counts


def get_sends_per_sender(days=30):
    """Count emails sent per sender_account per day over last N days."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("sender_account,sent_at")
        .not_.is_("sent_at", "null")
        .gte("sent_at", cutoff)
        .execute()
    )
    daily = {}  # {date: {account: count}}
    for row in (result.data or []):
        acc = row.get("sender_account") or "unknown"
        sent = row.get("sent_at", "")
        if sent:
            day = sent[:10]
            if day not in daily:
                daily[day] = {}
            daily[day][acc] = daily[day].get(acc, 0) + 1
    return daily


def get_sender_performance():
    """Per-sender: total sent, opened, replied, open_rate, reply_rate."""
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("sender_account,status,open_count")
        .not_.is_("sender_account", "null")
        .execute()
    )
    stats = {}
    for row in (result.data or []):
        acc = row.get("sender_account") or ""
        if not acc:
            continue
        if acc not in stats:
            stats[acc] = {"sent": 0, "opened": 0, "replied": 0}
        if row.get("status") in ("sent", "opened", "replied"):
            stats[acc]["sent"] += 1
        if row.get("status") in ("opened", "replied") or (row.get("open_count") or 0) > 0:
            stats[acc]["opened"] += 1
        if row.get("status") == "replied":
            stats[acc]["replied"] += 1

    for acc, s in stats.items():
        s["open_rate"] = round(s["opened"] / s["sent"] * 100, 1) if s["sent"] else 0
        s["reply_rate"] = round(s["replied"] / s["sent"] * 100, 1) if s["sent"] else 0
    return stats


def get_sequence_stats():
    """Per-touchpoint: sent count, open rate, reply rate."""
    sb = _get_client()
    result = sb.table("emails").select("touchpoint,status,open_count").execute()
    by_touch = {}
    for row in (result.data or []):
        t = row.get("touchpoint", 0)
        if t not in by_touch:
            by_touch[t] = {"sent": 0, "opened": 0, "replied": 0}
        if row.get("status") in ("sent", "opened", "replied"):
            by_touch[t]["sent"] += 1
        if row.get("status") in ("opened", "replied") or (row.get("open_count") or 0) > 0:
            by_touch[t]["opened"] += 1
        if row.get("status") == "replied":
            by_touch[t]["replied"] += 1

    for t, s in by_touch.items():
        s["open_rate"] = round(s["opened"] / s["sent"] * 100, 1) if s["sent"] else 0
        s["reply_rate"] = round(s["replied"] / s["sent"] * 100, 1) if s["sent"] else 0
    return by_touch


def get_daily_send_counts(days=30):
    """Actual email sends per day (using emails.sent_at)."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("sent_at")
        .not_.is_("sent_at", "null")
        .gte("sent_at", cutoff)
        .execute()
    )
    daily = {}
    for row in (result.data or []):
        sent = row.get("sent_at", "")
        if sent:
            day = sent[:10]
            daily[day] = daily.get(day, 0) + 1
    return daily


# ── Email Hub Queries ────────────────────────────────

def get_all_emails(status=None, search=None, sender=None, sort_by="created_at",
                   sort_dir="desc", page=1, per_page=50):
    """Paginated email listing with filters."""
    sb = _get_client()
    query = sb.table("emails").select("*", count="exact")
    if status:
        query = query.eq("status", status)
    if sender:
        query = query.eq("sender_account", sender)
    if search:
        s = f"%{search}%"
        query = query.or_(f"subject.ilike.{s},to_email.ilike.{s},slug.ilike.{s}")
    desc = sort_dir == "desc"
    query = query.order(sort_by, desc=desc)
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)
    result = query.execute()
    return result.data or [], result.count if result.count is not None else len(result.data or [])


def get_all_replies(sentiment=None, limit=100):
    """All replies with optional sentiment filter."""
    sb = _get_client()
    query = sb.table("replies").select("*")
    if sentiment:
        query = query.eq("sentiment", sentiment)
    query = query.order("received_at", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


def get_bounced_emails(limit=100):
    """Emails with status='bounced'."""
    sb = _get_client()
    result = (
        sb.table("emails")
        .select("*")
        .eq("status", "bounced")
        .order("sent_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_recent_sent_emails(sender=None, limit=50):
    """Recent sent emails with optional sender filter."""
    sb = _get_client()
    query = sb.table("emails").select("*").in_("status", ["sent", "opened", "replied"])
    if sender:
        query = query.eq("sender_account", sender)
    query = query.order("sent_at", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


# ── Dashboard Aggregates ─────────────────────────────

def get_pipeline_throughput(days=30):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sb = _get_client()
    result = (
        sb.table("pipeline_runs")
        .select("completed_at")
        .eq("status", "completed")
        .gte("completed_at", cutoff)
        .execute()
    )
    daily = {}
    for row in (result.data or []):
        completed = row.get("completed_at", "")
        if completed:
            day = completed[:10]
            daily[day] = daily.get(day, 0) + 1
    return daily
