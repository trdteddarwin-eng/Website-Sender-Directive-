"""Data layer — Google Sheets for leads, local JSON files for operational data."""

import os
import sys
import re
import json
import uuid
import time
import hashlib
import threading
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    GOOGLE_SHEET_ID, GOOGLE_TOKEN_PATH, GOOGLE_CREDS_PATH, LOCAL_DATA_DIR, WORKSPACE_ROOT
)

# ── Google Sheets Cache ───────────────────────────────

_CACHE_TTL = 60  # seconds

class _SheetCache:
    """Caches all rows from the Google Sheet with a TTL."""

    def __init__(self):
        self._rows = []          # list of dicts (one per row)
        self._headers = []       # column headers
        self._worksheet = None   # gspread worksheet handle
        self._loaded_at = 0
        self._lock = threading.Lock()

    def _get_worksheet(self):
        if self._worksheet is not None:
            return self._worksheet
        import gspread
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = None
        token_path = GOOGLE_TOKEN_PATH
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            else:
                raise RuntimeError(
                    "Google OAuth token not found or invalid. "
                    "Run execution/read_sheet.py once to authenticate."
                )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        self._worksheet = spreadsheet.sheet1
        return self._worksheet

    def _load(self):
        ws = self._get_worksheet()
        records = ws.get_all_records()
        self._headers = ws.row_values(1)
        self._rows = records
        self._loaded_at = time.time()

    def get_rows(self):
        with self._lock:
            if not self._rows or (time.time() - self._loaded_at) > _CACHE_TTL:
                self._load()
            return list(self._rows)

    def get_headers(self):
        with self._lock:
            if not self._headers:
                self._load()
            return list(self._headers)

    def invalidate(self):
        with self._lock:
            self._loaded_at = 0

    def update_cell_by_row(self, row_index_1based, col_name, value):
        """Update a single cell in the sheet. row_index_1based is 1-indexed (row 1 = header)."""
        ws = self._get_worksheet()
        headers = self.get_headers()
        if col_name not in headers:
            return
        col_idx = headers.index(col_name) + 1  # gspread is 1-indexed
        ws.update_cell(row_index_1based, col_idx, value)
        self.invalidate()

    def find_row_index(self, slug):
        """Find the 1-based row index for a slug. Row 1 is header, so data starts at 2."""
        rows = self.get_rows()
        for i, row in enumerate(rows):
            if _slugify(row.get("company_name", "")) == slug:
                return i + 2  # +2 because: 0-indexed list + header row
        return None

    def get_worksheet_direct(self):
        return self._get_worksheet()


_cache = _SheetCache()


def _slugify(company_name):
    if not company_name:
        return ""
    name = str(company_name).split(",")[0].strip()
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _make_id(slug):
    """Deterministic UUID from slug so IDs are stable across cache reloads."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lead.{slug}"))


def _row_to_lead(row):
    """Convert a sheet row dict into the app's lead format."""
    company = row.get("company_name", "")
    slug = _slugify(company)
    if not slug:
        return None

    # Parse is_qualified
    iq = row.get("is_qualified_hvac", "")
    if isinstance(iq, str):
        is_qualified = iq.lower() in ("yes", "true", "1")
    else:
        is_qualified = bool(iq)

    # Parse lead_score
    score = row.get("lead_score", 0)
    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0

    # Parse send_status → pipeline_status
    send_status = str(row.get("send_status", "")).lower().strip()
    status_map = {
        "": "pending",
        "pending": "pending",
        "sent": "emailing",
        "emailing": "emailing",
        "completed": "completed",
        "failed": "failed",
        "researching": "researching",
        "designing": "designing",
        "reviewing": "reviewing",
        "deploying": "deploying",
    }
    pipeline_status = status_map.get(send_status, send_status or "pending")

    # Build raw_data from all columns
    raw_data = {k: v for k, v in row.items()}

    lead = {
        "id": _make_id(slug),
        "slug": slug,
        "first_name": str(row.get("first_name", "")),
        "last_name": str(row.get("last_name", "")),
        "full_name": str(row.get("full_name", "")),
        "email": str(row.get("email", "")),
        "phone": str(row.get("phone", "")),
        "company_name": company,
        "website": str(row.get("website", "")),
        "city": str(row.get("city", "")),
        "state": str(row.get("state", "")),
        "industry": str(row.get("industry", "")),
        "employee_count": row.get("employee_count", ""),
        "lead_score": score,
        "lead_tier": str(row.get("lead_tier", "")).lower().strip(),
        "score_breakdown": str(row.get("score_breakdown", "")),
        "is_qualified": is_qualified,
        "disqualification_reason": str(row.get("disqualification_reason", "")),
        "company_description": str(row.get("company_description", "")),
        "pipeline_status": pipeline_status,
        "send_step": row.get("send_step", ""),
        "raw_data": raw_data,
    }
    return lead


# ── Local JSON Storage ────────────────────────────────

_json_locks = {}
_json_meta_lock = threading.Lock()


def _get_json_lock(table_name):
    with _json_meta_lock:
        if table_name not in _json_locks:
            _json_locks[table_name] = threading.Lock()
        return _json_locks[table_name]


def _json_path(table_name):
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    return os.path.join(LOCAL_DATA_DIR, f"{table_name}.json")


def _read_json(table_name):
    path = _json_path(table_name)
    lock = _get_json_lock(table_name)
    with lock:
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []


def _write_json(table_name, data):
    path = _json_path(table_name)
    lock = _get_json_lock(table_name)
    with lock:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=_ser)


def _ser(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _insert_json(table_name, record):
    if "id" not in record:
        record["id"] = str(uuid.uuid4())
    if "created_at" not in record:
        record["created_at"] = datetime.utcnow().isoformat()
    rows = _read_json(table_name)
    rows.append(record)
    _write_json(table_name, rows)
    return record


def _update_json(table_name, record_id, updates):
    rows = _read_json(table_name)
    for row in rows:
        if row.get("id") == record_id:
            row.update(updates)
            _write_json(table_name, rows)
            return row
    return None


def _find_json(table_name, key, value):
    rows = _read_json(table_name)
    for row in rows:
        if row.get(key) == value:
            return row
    return None


# ── Leads (from Google Sheets) ────────────────────────

def get_leads(tier=None, status=None, search=None, sort_by="lead_score",
              sort_dir="desc", page=1, per_page=50):
    """Fetch leads with optional filters, search, sorting, pagination."""
    rows = _cache.get_rows()
    leads = []
    for row in rows:
        lead = _row_to_lead(row)
        if not lead:
            continue
        if tier and lead.get("lead_tier") != tier:
            continue
        if status and lead.get("pipeline_status") != status:
            continue
        if search:
            s = search.lower()
            searchable = f"{lead.get('company_name','')} {lead.get('first_name','')} {lead.get('last_name','')} {lead.get('city','')}".lower()
            if s not in searchable:
                continue
        leads.append(lead)

    # Sort
    reverse = sort_dir == "desc"
    def sort_key(l):
        val = l.get(sort_by, "")
        if isinstance(val, str):
            try:
                return float(val)
            except (ValueError, TypeError):
                return val.lower()
        if val is None:
            return ""
        return val
    leads.sort(key=sort_key, reverse=reverse)

    total = len(leads)
    offset = (page - 1) * per_page
    page_leads = leads[offset:offset + per_page]
    return page_leads, total


def get_lead_by_slug(slug):
    rows = _cache.get_rows()
    for row in rows:
        lead = _row_to_lead(row)
        if lead and lead["slug"] == slug:
            return lead
    return None


def get_lead_by_id(lead_id):
    rows = _cache.get_rows()
    for row in rows:
        lead = _row_to_lead(row)
        if lead and lead["id"] == lead_id:
            return lead
    return None


def upsert_lead(data):
    """Insert or update a lead in the sheet."""
    slug = data.get("slug", "")
    if not slug:
        return None

    row_idx = _cache.find_row_index(slug)
    ws = _cache.get_worksheet_direct()
    headers = _cache.get_headers()

    if row_idx:
        # Update existing row
        for col_name, value in data.items():
            if col_name in ("id", "slug", "raw_data", "pipeline_status"):
                continue
            if col_name in headers:
                col_idx = headers.index(col_name) + 1
                ws.update_cell(row_idx, col_idx, str(value) if value is not None else "")
        _cache.invalidate()
        return get_lead_by_slug(slug)
    else:
        # Append new row
        new_row = []
        for h in headers:
            val = data.get(h, "")
            new_row.append(str(val) if val is not None else "")
        ws.append_row(new_row)
        _cache.invalidate()
        return get_lead_by_slug(slug)


def update_lead(slug, updates):
    """Update specific fields for a lead in the sheet."""
    row_idx = _cache.find_row_index(slug)
    if not row_idx:
        return None

    headers = _cache.get_headers()

    # Map app fields back to sheet columns
    field_to_col = {
        "pipeline_status": "send_status",
        "is_qualified": "is_qualified_hvac",
    }

    for field, value in updates.items():
        col_name = field_to_col.get(field, field)
        if col_name not in headers:
            continue
        # Convert values back to sheet format
        if field == "pipeline_status":
            status_reverse = {
                "pending": "",
                "researching": "researching",
                "designing": "designing",
                "reviewing": "reviewing",
                "deploying": "deploying",
                "emailing": "sent",
                "completed": "completed",
                "failed": "failed",
            }
            value = status_reverse.get(value, value)
        elif field == "is_qualified":
            value = "yes" if value else "no"
        _cache.update_cell_by_row(row_idx, col_name, str(value) if value is not None else "")

    _cache.invalidate()
    return get_lead_by_slug(slug)


def get_next_unprocessed_lead():
    """Get the highest-scored HOT lead that hasn't been processed yet."""
    rows = _cache.get_rows()
    candidates = []
    for row in rows:
        lead = _row_to_lead(row)
        if not lead:
            continue
        if (lead.get("lead_tier") == "hot"
                and lead.get("pipeline_status") == "pending"
                and lead.get("is_qualified")):
            candidates.append(lead)
    if not candidates:
        return None
    candidates.sort(key=lambda l: l.get("lead_score", 0), reverse=True)
    return candidates[0]


def get_lead_counts():
    """Get counts by tier and status for dashboard KPIs."""
    rows = _cache.get_rows()
    leads = [_row_to_lead(row) for row in rows]
    leads = [l for l in leads if l]
    return {
        "total": len(leads),
        "hot": sum(1 for l in leads if l.get("lead_tier") == "hot"),
        "warm": sum(1 for l in leads if l.get("lead_tier") == "warm"),
        "cold": sum(1 for l in leads if l.get("lead_tier") not in ("hot", "warm") and l.get("lead_tier")),
        "pending": sum(1 for l in leads if l.get("pipeline_status") == "pending"),
        "completed": sum(1 for l in leads if l.get("pipeline_status") == "completed"),
        "processing": sum(1 for l in leads if l.get("pipeline_status") not in ("pending", "completed", "failed")),
        "failed": sum(1 for l in leads if l.get("pipeline_status") == "failed"),
    }


# ── Pipeline Runs (from local JSON) ──────────────────

def create_pipeline_run(lead_id, slug, palette_index, hero_style_index):
    data = {
        "lead_id": lead_id,
        "slug": slug,
        "status": "running",
        "palette_index": palette_index,
        "hero_style_index": hero_style_index,
        "started_at": datetime.utcnow().isoformat(),
        "agents": {
            "researcher": {"status": "waiting", "task": "", "completed_tasks": []},
            "designer": {"status": "waiting", "task": "", "completed_tasks": []},
            "judge": {"status": "waiting", "task": "", "completed_tasks": []},
            "ops": {"status": "waiting", "task": "", "completed_tasks": []},
        },
        "log": [],
    }
    return _insert_json("pipeline_runs", data)


def get_pipeline_run(run_id):
    return _find_json("pipeline_runs", "id", run_id)


def get_active_pipeline_run():
    rows = _read_json("pipeline_runs")
    running = [r for r in rows if r.get("status") == "running"]
    if not running:
        return None
    running.sort(key=lambda r: r.get("started_at", ""), reverse=True)
    return running[0]


def update_pipeline_run(run_id, updates):
    return _update_json("pipeline_runs", run_id, updates)


def get_recent_pipeline_runs(limit=10):
    rows = _read_json("pipeline_runs")
    rows.sort(key=lambda r: r.get("started_at", ""), reverse=True)
    return rows[:limit]


# ── Spec Sites (from local JSON) ─────────────────────

def create_spec_site(data):
    return _insert_json("spec_sites", data)


def get_spec_site_by_lead(lead_id):
    rows = _read_json("spec_sites")
    matches = [r for r in rows if r.get("lead_id") == lead_id]
    if not matches:
        return None
    matches.sort(key=lambda r: r.get("deployed_at", r.get("created_at", "")), reverse=True)
    return matches[0]


# ── Emails (from local JSON) ─────────────────────────

def create_email(data):
    return _insert_json("emails", data)


def get_emails_for_lead(lead_id):
    rows = _read_json("emails")
    matches = [r for r in rows if r.get("lead_id") == lead_id]
    matches.sort(key=lambda r: r.get("touchpoint", 0))
    return matches


def update_email(email_id, updates):
    return _update_json("emails", email_id, updates)


def get_emails_by_status(status, limit=50):
    rows = _read_json("emails")
    matches = [r for r in rows if r.get("status") == status]
    matches.sort(key=lambda r: r.get("scheduled_send_date", ""))
    return matches[:limit]


def get_email_by_id(email_id):
    return _find_json("emails", "id", email_id)


def get_email_stats():
    rows = _read_json("emails")
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


# ── Email Sequences (from local JSON) ────────────────

def create_sequence(data):
    slug = data.get("slug", "")
    if slug:
        existing = _find_json("email_sequences", "slug", slug)
        if existing:
            _update_json("email_sequences", existing["id"], data)
            return {**existing, **data}
    return _insert_json("email_sequences", data)


def get_sequence_by_slug(slug):
    return _find_json("email_sequences", "slug", slug)


def get_active_sequences():
    rows = _read_json("email_sequences")
    matches = [r for r in rows if r.get("status") == "active"]
    matches.sort(key=lambda r: r.get("next_send_date", ""))
    return matches


def get_due_sequences(today=None):
    if today is None:
        today = date.today().isoformat()
    rows = _read_json("email_sequences")
    matches = [r for r in rows if r.get("status") == "active" and r.get("next_send_date", "9999") <= today]
    matches.sort(key=lambda r: r.get("next_send_date", ""))
    return matches


def update_sequence(seq_id, updates):
    return _update_json("email_sequences", seq_id, updates)


def get_all_sequences(status=None, limit=100):
    rows = _read_json("email_sequences")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    rows.sort(key=lambda r: r.get("started_at", r.get("created_at", "")), reverse=True)
    return rows[:limit]


# ── Replies (from local JSON) ────────────────────────

def create_reply(data):
    return _insert_json("replies", data)


def get_replies_for_lead(lead_id):
    rows = _read_json("replies")
    matches = [r for r in rows if r.get("lead_id") == lead_id]
    matches.sort(key=lambda r: r.get("received_at", ""), reverse=True)
    return matches


def get_reply_stats():
    rows = _read_json("replies")
    return {
        "total": len(rows),
        "positive": sum(1 for r in rows if r.get("sentiment") == "positive"),
        "negative": sum(1 for r in rows if r.get("sentiment") == "negative"),
        "neutral": sum(1 for r in rows if r.get("sentiment") == "neutral"),
        "out_of_office": sum(1 for r in rows if r.get("sentiment") == "out_of_office"),
    }


# ── Activity Log (from local JSON) ───────────────────

def log_activity(lead_id=None, slug=None, event_type="", event_data=None,
                 agent=None, message=None):
    data = {
        "lead_id": lead_id,
        "slug": slug,
        "event_type": event_type,
        "event_data": event_data or {},
        "agent": agent,
        "message": message,
    }
    return _insert_json("activity_log", data)


def get_recent_activity(limit=50, lead_id=None):
    rows = _read_json("activity_log")
    if lead_id:
        rows = [r for r in rows if r.get("lead_id") == lead_id]
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[:limit]


def get_activity_for_slug(slug, limit=100):
    rows = _read_json("activity_log")
    matches = [r for r in rows if r.get("slug") == slug]
    matches.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return matches[:limit]


# ── Dashboard Aggregates ─────────────────────────────

def get_pipeline_throughput(days=30):
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = _read_json("pipeline_runs")
    daily = {}
    for row in rows:
        if row.get("status") == "completed" and row.get("completed_at", "") >= cutoff:
            day = row["completed_at"][:10]
            daily[day] = daily.get(day, 0) + 1
    return daily
