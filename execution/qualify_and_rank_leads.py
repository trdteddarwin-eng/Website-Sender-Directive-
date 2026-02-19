#!/usr/bin/env python3
"""
Qualify & Rank HVAC Leads

Phase 1: Classify leads as qualified/not-qualified HVAC businesses
  - Deterministic pre-filter (employee count, keywords)
  - Claude Haiku batch classification

Phase 2: Enrich with website, LinkedIn, Instagram data + score/rank
  - 2a: Scrape websites (requests + BeautifulSoup)
  - 2b: LinkedIn company profiles (Bright Data Datasets API)
  - 2c: Find Instagram handles (from website scrape)
  - 2d: Instagram profiles (Bright Data Datasets API)
  - 2e: Deterministic scoring (100-point rubric)

Usage:
    python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase 1
    python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase 2
    python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase both
    python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase both --start_row 2 --end_row 11 --dry_run
"""

import os
import sys
import json
import argparse
import time
import re
import requests as http_requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import anthropic
from bs4 import BeautifulSoup

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BRIGHTDATA_API_TOKEN = os.getenv("BRIGHTDATA_API_TOKEN", "")
MODEL = "claude-3-5-haiku-20241022"
OPENROUTER_MODEL = "anthropic/claude-3.5-haiku"

BATCH_SIZE = 20          # Leads per Claude classification batch
MAX_RETRIES = 3
MIN_DELAY = 0.5          # Seconds between API calls

# Bright Data Dataset IDs
LINKEDIN_DATASET_ID = "gd_l1vikfnt1wgvvqz95w"
INSTAGRAM_DATASET_ID = "gd_l1vikfch901nx3by4"

# Output columns per phase
PHASE1_COLUMNS = ["is_qualified_hvac", "disqualification_reason"]
PHASE2_COLUMNS = [
    "linkedin_followers", "linkedin_last_post",
    "instagram_handle", "instagram_followers", "instagram_last_post",
    "has_chatbot", "has_online_booking",
    "website_quality_notes", "social_media_notes",
    "lead_score", "lead_tier", "score_breakdown",
]

sheet_lock = Lock()


# ── Google Sheets I/O ───────────────────────────────────────────────────────

def extract_sheet_id(url):
    if "/d/" in url:
        return url.split("/d/")[1].split("/")[0]
    return url


def get_credentials():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = None
    if os.path.exists("token.json"):
        try:
            with open("token.json", "r") as f:
                creds = Credentials.from_authorized_user_info(json.load(f), scopes)
        except Exception as e:
            print(f"Error loading token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow

            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json"), scopes
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def column_letter(n):
    result = ""
    while n >= 0:
        result = chr(65 + (n % 26)) + result
        n = n // 26 - 1
    return result


def read_leads(sheet_url, worksheet_name=None, start_row=None, end_row=None):
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet_id = extract_sheet_id(sheet_url)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = (
        spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.sheet1
    )

    all_values = worksheet.get_all_values()
    if not all_values:
        return worksheet, [], []

    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:]):
        row_num = i + 2  # 1-indexed, header is row 1
        if start_row and row_num < start_row:
            continue
        if end_row and row_num > end_row:
            continue
        rows.append((row_num, row))

    return worksheet, headers, rows


def ensure_columns(worksheet, headers, new_cols):
    current = list(headers)
    added = []
    for col in new_cols:
        if col not in current:
            current.append(col)
            added.append(col)
    if added:
        if len(current) > worksheet.col_count:
            worksheet.resize(cols=len(current))
        updates = []
        for col in added:
            idx = current.index(col)
            updates.append({"range": f"{column_letter(idx)}1", "values": [[col]]})
        worksheet.batch_update(updates)
        print(f"Added columns: {', '.join(added)}")
    return current


def get_col_val(row, headers, names):
    for name in names:
        try:
            idx = headers.index(name)
            if len(row) > idx:
                return row[idx].strip()
        except ValueError:
            continue
    return ""


def update_row(worksheet, headers, row_num, data, columns, dry_run=False):
    updates = []
    for col in columns:
        try:
            idx = headers.index(col)
            val = data.get(col, "")
            if val is not None:
                updates.append(
                    {
                        "range": f"{column_letter(idx)}{row_num}",
                        "values": [[str(val)[:50000]]],
                    }
                )
        except ValueError:
            continue
    if updates and not dry_run:
        with sheet_lock:
            worksheet.batch_update(updates)
    return len(updates)


# ── Claude API ──────────────────────────────────────────────────────────────

def _call_openrouter(prompt, max_tokens):
    """Call Claude via OpenRouter (OpenAI-compatible API)."""
    resp = http_requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def call_claude(prompt, max_tokens=4000, retry_count=0):
    """Call Claude Haiku. Tries Anthropic SDK first, auto-falls back to OpenRouter."""
    text = None
    try:
        # Try Anthropic SDK first if key looks real
        if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "PASTE_YOUR_ANTHROPIC_API_KEY_HERE":
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            msg = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text.strip()
        elif OPENROUTER_API_KEY:
            text = _call_openrouter(prompt, max_tokens)
        else:
            raise ValueError(
                "No API key found. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in .env"
            )

    except anthropic.AuthenticationError:
        # Anthropic key invalid/expired — fall back to OpenRouter
        if OPENROUTER_API_KEY:
            if retry_count == 0:
                print("  Anthropic key invalid, falling back to OpenRouter...")
            text = _call_openrouter(prompt, max_tokens)
        else:
            raise

    except (anthropic.RateLimitError, http_requests.exceptions.HTTPError):
        if retry_count < MAX_RETRIES:
            wait = (2 ** retry_count) * 2
            print(f"  Rate limited, retrying in {wait}s...")
            time.sleep(wait)
            return call_claude(prompt, max_tokens, retry_count + 1)
        raise

    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"  API error: {e}, retrying...")
            time.sleep(1)
            return call_claude(prompt, max_tokens, retry_count + 1)
        raise

    # Strip markdown code blocks
    if text and text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        for i, line in enumerate(lines):
            if i > 0 and line.strip() == "```":
                end = i
                break
        text = "\n".join(lines[1:end])

    return text


def call_claude_json(prompt, max_tokens=4000):
    """Call Claude and parse JSON response with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            text = call_claude(prompt, max_tokens)
            return json.loads(text)
        except json.JSONDecodeError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  JSON parse error, retrying... ({e})")
                time.sleep(1)
            else:
                print(f"  Failed to parse JSON after {MAX_RETRIES} attempts")
                return None


# ── Phase 1: Qualify ────────────────────────────────────────────────────────

DISQUALIFY_KEYWORDS = [
    "manufacturer",
    "distributor",
    "wholesaler",
    "wholesale",
    "supply chain",
    "staffing",
    "recruiting",
    "recruitment",
    "software",
    "saas",
]


def deterministic_prefilter(row, headers):
    """Quick rules-based filter. Returns (qualified, reason) or (None, None) for AI."""
    company_name = get_col_val(
        row, headers, ["company_name", "business_name", "name"]
    )
    emp_str = get_col_val(
        row,
        headers,
        ["company_employee_count", "employee_count", "employees"],
    )
    description = get_col_val(
        row, headers, ["company_description", "description", "about"]
    ).lower()
    industry = get_col_val(
        row, headers, ["company_industry", "industry"]
    ).lower()

    if not company_name:
        return False, "No company name"

    # Parse employee count
    emp_count = 0
    if emp_str:
        try:
            emp_count = int(re.sub(r"[^\d]", "", emp_str))
        except ValueError:
            pass

    if emp_count >= 500:
        return False, f"Enterprise - too large ({emp_count} employees)"

    for kw in DISQUALIFY_KEYWORDS:
        if kw in description or kw in industry:
            return False, f"Not a service company ({kw} in description/industry)"

    # Needs AI classification
    return None, None


def batch_classify_leads(leads_batch, batch_num, total_batches):
    """Use Claude Haiku to classify a batch of leads as HVAC or not."""
    records = []
    for lead in leads_batch:
        records.append(
            {
                "row_num": lead["row_num"],
                "company_name": lead["company_name"],
                "job_title": lead.get("job_title", ""),
                "description": lead.get("description", "")[:200],
                "industry": lead.get("industry", ""),
                "employee_count": lead.get("employee_count", ""),
                "website": lead.get("website", ""),
            }
        )

    prompt = f"""Classify each company as a qualified HVAC lead or not.

QUALIFIED = local/regional HVAC service company (installs, repairs, maintains heating/cooling systems), under 500 employees.

NOT QUALIFIED (with reason):
- Manufacturer (makes HVAC equipment, not service)
- Distributor/wholesaler (sells parts, not service)
- Software company
- Staffing/recruiting firm
- National chain (Carrier corporate, Trane corporate)
- Non-HVAC business
- Consulting/engineering firm (unless they also do HVAC service)

IMPORTANT: Companies that DO HVAC installation, repair, maintenance, or service ARE qualified even if they also do plumbing, electrical, etc. Mechanical contractors that do HVAC work ARE qualified.

Input leads:
{json.dumps(records, indent=2)}

Return ONLY a valid JSON array:
[{{"row_num": N, "qualified": true, "reason": ""}}]
Each object must have row_num (number), qualified (boolean), reason (string, empty if qualified)."""

    print(f"  Classifying batch {batch_num}/{total_batches} ({len(leads_batch)} leads)...")
    result = call_claude_json(prompt, max_tokens=4000)

    if not result:
        return [
            {
                "row_num": l["row_num"],
                "qualified": True,
                "reason": "AI classification failed - defaulting to qualified",
            }
            for l in leads_batch
        ]

    # Ensure all rows have results
    result_map = {r["row_num"]: r for r in result}
    final = []
    for lead in leads_batch:
        if lead["row_num"] in result_map:
            final.append(result_map[lead["row_num"]])
        else:
            final.append(
                {
                    "row_num": lead["row_num"],
                    "qualified": True,
                    "reason": "Missing from AI response - defaulting to qualified",
                }
            )

    return final


def batch_update_rows(worksheet, headers, row_updates, columns, dry_run=False):
    """Write multiple rows to sheet in chunked batches (avoids rate limits)."""
    if not row_updates or dry_run:
        return

    all_updates = []
    for row_num, data in row_updates:
        for col in columns:
            try:
                idx = headers.index(col)
                val = data.get(col, "")
                if val is not None:
                    all_updates.append(
                        {
                            "range": f"{column_letter(idx)}{row_num}",
                            "values": [[str(val)[:50000]]],
                        }
                    )
            except ValueError:
                continue

    # Write in chunks of 500 cells with pauses to avoid rate limits
    chunk_size = 500
    for i in range(0, len(all_updates), chunk_size):
        chunk = all_updates[i : i + chunk_size]
        with sheet_lock:
            worksheet.batch_update(chunk)
        if i + chunk_size < len(all_updates):
            time.sleep(2)  # Pause between chunks to respect rate limits

    print(f"  Wrote {len(all_updates)} cells to sheet")


def run_phase1(worksheet, headers, rows, dry_run=False):
    """Phase 1: Qualify leads as HVAC service companies."""
    print(f"\n{'='*60}")
    print("PHASE 1: QUALIFY LEADS")
    print(f"{'='*60}")
    print(f"Total leads to process: {len(rows)}\n")

    if not dry_run:
        headers = ensure_columns(worksheet, headers, PHASE1_COLUMNS)

    qualified_col_exists = "is_qualified_hvac" in headers
    needs_ai = []
    pending_writes = []  # Collect all writes, flush in batches
    stats = {
        "prefilter_disqualified": 0,
        "ai_qualified": 0,
        "ai_disqualified": 0,
        "skipped": 0,
    }

    for row_num, row in rows:
        # Skip already classified
        if qualified_col_exists:
            existing = get_col_val(row, headers, ["is_qualified_hvac"])
            if existing:
                stats["skipped"] += 1
                continue

        company_name = get_col_val(
            row, headers, ["company_name", "business_name", "name"]
        )
        qualified, reason = deterministic_prefilter(row, headers)

        if qualified is False:
            stats["prefilter_disqualified"] += 1
            data = {"is_qualified_hvac": "no", "disqualification_reason": reason}
            pending_writes.append((row_num, data))
            print(f"  [Row {row_num}] {company_name} -> DISQUALIFIED (pre-filter): {reason}")
        elif qualified is None:
            needs_ai.append(
                {
                    "row_num": row_num,
                    "company_name": company_name,
                    "job_title": get_col_val(
                        row, headers, ["job_title", "title", "position"]
                    ),
                    "description": get_col_val(
                        row,
                        headers,
                        ["company_description", "description", "about"],
                    ),
                    "industry": get_col_val(
                        row, headers, ["company_industry", "industry"]
                    ),
                    "employee_count": get_col_val(
                        row,
                        headers,
                        ["company_employee_count", "employee_count", "employees"],
                    ),
                    "website": get_col_val(
                        row,
                        headers,
                        ["website", "company_domain", "domain", "url"],
                    ),
                }
            )

    # Flush pre-filter results to sheet
    print(f"\nPre-filter results:")
    print(f"  Skipped (already classified): {stats['skipped']}")
    print(f"  Disqualified (pre-filter): {stats['prefilter_disqualified']}")
    print(f"  Needs AI classification: {len(needs_ai)}")

    if pending_writes:
        print(f"\n  Writing {len(pending_writes)} pre-filter results to sheet...")
        batch_update_rows(worksheet, headers, pending_writes, PHASE1_COLUMNS, dry_run)
        pending_writes = []

    # AI classification in batches of BATCH_SIZE
    if needs_ai:
        batches = [
            needs_ai[i : i + BATCH_SIZE]
            for i in range(0, len(needs_ai), BATCH_SIZE)
        ]
        total_batches = len(batches)

        for batch_idx, batch in enumerate(batches):
            results = batch_classify_leads(batch, batch_idx + 1, total_batches)

            for r in results:
                row_num = r["row_num"]
                company = next(
                    (l["company_name"] for l in batch if l["row_num"] == row_num),
                    "Unknown",
                )

                if r.get("qualified", False):
                    stats["ai_qualified"] += 1
                    data = {"is_qualified_hvac": "yes", "disqualification_reason": ""}
                    print(f"  [Row {row_num}] {company} -> QUALIFIED")
                else:
                    stats["ai_disqualified"] += 1
                    reason = r.get("reason", "AI classified as not HVAC")
                    data = {
                        "is_qualified_hvac": "no",
                        "disqualification_reason": reason,
                    }
                    print(f"  [Row {row_num}] {company} -> DISQUALIFIED: {reason}")

                pending_writes.append((row_num, data))

            # Flush after each AI batch
            if pending_writes:
                batch_update_rows(
                    worksheet, headers, pending_writes, PHASE1_COLUMNS, dry_run
                )
                pending_writes = []

            time.sleep(MIN_DELAY)

    total_qualified = stats["ai_qualified"]
    total_disqualified = stats["prefilter_disqualified"] + stats["ai_disqualified"]

    print(f"\n{'='*60}")
    print("PHASE 1 COMPLETE")
    print(f"{'='*60}")
    print(f"Qualified: {total_qualified}")
    print(f"Disqualified: {total_disqualified}")
    print(f"Skipped (already done): {stats['skipped']}")
    if dry_run:
        print("[DRY RUN] No changes written to sheet")

    return headers, stats


# ── Phase 2: Enrich & Score ─────────────────────────────────────────────────

def scrape_website_simple(url, timeout=15):
    """Scrape a website and extract signals (chatbot, booking, social links, SEO)."""
    if not url:
        return None

    if not url.startswith("http"):
        url = "https://" + url

    try:
        resp = http_requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        result = {
            "status": resp.status_code,
            "title": (
                soup.title.string.strip() if soup.title and soup.title.string else ""
            ),
            "meta_description": "",
            "has_chatbot": False,
            "has_booking": False,
            "social_links": {},
            "text_content": "",
        }

        # Meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            result["meta_description"] = meta.get("content", "")

        page_lower = resp.text.lower()

        # Chatbot indicators
        chatbot_kws = [
            "tawk", "drift", "intercom", "hubspot-messages",
            "livechat", "zendesk", "crisp", "tidio",
            "freshchat", "olark", "chat-widget", "chatbot",
            "liveagent", "podium",
        ]
        for kw in chatbot_kws:
            if kw in page_lower:
                result["has_chatbot"] = True
                break

        # Booking system indicators
        booking_kws = [
            "book online", "schedule now", "book now", "book appointment",
            "calendly", "acuity", "schedulicity", "housecallpro",
            "housecall pro", "jobber", "servicetitan",
            "schedule service", "request appointment",
        ]
        for kw in booking_kws:
            if kw in page_lower:
                result["has_booking"] = True
                break

        # Social media links
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if "instagram.com" in href:
                m = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", href)
                if m and m.group(1) not in ("p", "explore", "reels", "stories"):
                    result["social_links"]["instagram"] = m.group(1)
            elif "linkedin.com/company" in href:
                m = re.search(r"linkedin\.com/company/([a-zA-Z0-9-]+)", href)
                if m:
                    result["social_links"]["linkedin"] = m.group(1)
            elif "facebook.com" in href:
                m = re.search(r"facebook\.com/([a-zA-Z0-9.]+)", href)
                if m and m.group(1) not in ("sharer", "share", "dialog", "tr"):
                    result["social_links"]["facebook"] = m.group(1)

        result["text_content"] = soup.get_text(separator=" ", strip=True)[:3000]
        return result

    except http_requests.exceptions.ConnectionError:
        return {"status": 0, "error": "Connection failed - site may be down"}
    except http_requests.exceptions.Timeout:
        return {"status": 0, "error": "Timeout"}
    except http_requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else 0
        return {"status": code, "error": str(e)}
    except Exception as e:
        return {"status": 0, "error": str(e)}


# ── Bright Data Datasets API ───────────────────────────────────────────────

def trigger_brightdata_dataset(dataset_id, input_data):
    """Trigger a Bright Data dataset collection. Returns snapshot_id."""
    if not BRIGHTDATA_API_TOKEN:
        print("  BRIGHTDATA_API_TOKEN not set - skipping dataset call")
        return None

    url = (
        f"https://api.brightdata.com/datasets/v3/trigger"
        f"?dataset_id={dataset_id}&include_errors=true"
        f"&type=discover_new&discover_by=url"
    )
    try:
        resp = http_requests.post(
            url,
            headers={
                "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json=input_data,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("snapshot_id")
    except Exception as e:
        print(f"  Bright Data trigger error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"  Response: {e.response.text[:300]}")
        return None


def poll_brightdata_snapshot(snapshot_id, max_wait=300):
    """Poll for Bright Data dataset results. Returns data list or None."""
    if not snapshot_id:
        return None

    url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
    headers = {"Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}"}

    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = http_requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 202:
                elapsed = int(time.time() - start)
                print(f"    Still processing... ({elapsed}s)")
                time.sleep(10)
            else:
                print(f"  Snapshot error: {resp.status_code} {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"  Snapshot poll error: {e}")
            time.sleep(10)

    print(f"  Snapshot {snapshot_id} timed out after {max_wait}s")
    return None


def fetch_linkedin_profiles(linkedin_urls):
    """Batch fetch LinkedIn company profiles via Bright Data Datasets API."""
    if not linkedin_urls:
        return {}

    input_data = [{"url": u} for u in linkedin_urls]
    print(f"  Triggering LinkedIn dataset for {len(input_data)} profiles...")

    snapshot_id = trigger_brightdata_dataset(LINKEDIN_DATASET_ID, input_data)
    if not snapshot_id:
        return {}

    print(f"  LinkedIn snapshot: {snapshot_id}, polling...")
    results = poll_brightdata_snapshot(snapshot_id, max_wait=300)
    if not results:
        return {}

    profile_map = {}
    for item in results:
        url = item.get("url", item.get("input", {}).get("url", ""))
        if url:
            profile_map[url.rstrip("/")] = item

    print(f"  LinkedIn: got {len(profile_map)} profiles")
    return profile_map


def fetch_instagram_profiles(instagram_urls):
    """Batch fetch Instagram profiles via Bright Data Datasets API."""
    if not instagram_urls:
        return {}

    input_data = [{"url": u} for u in instagram_urls]
    print(f"  Triggering Instagram dataset for {len(input_data)} profiles...")

    snapshot_id = trigger_brightdata_dataset(INSTAGRAM_DATASET_ID, input_data)
    if not snapshot_id:
        return {}

    print(f"  Instagram snapshot: {snapshot_id}, polling...")
    results = poll_brightdata_snapshot(snapshot_id, max_wait=300)
    if not results:
        return {}

    profile_map = {}
    for item in results:
        url = item.get("url", item.get("input", {}).get("url", ""))
        if url:
            profile_map[url.rstrip("/")] = item

    print(f"  Instagram: got {len(profile_map)} profiles")
    return profile_map


# ── Website Quality Analysis ───────────────────────────────────────────────

def analyze_website_quality(website_data, company_name):
    """Use Claude Haiku to rate website quality and SEO."""
    if not website_data or website_data.get("error"):
        if website_data and website_data.get("status") == 0:
            return {
                "website_quality": 0,
                "seo_quality": 0,
                "notes": f"Website DOWN: {website_data.get('error', 'unreachable')}",
            }
        return None

    prompt = f"""Rate this HVAC company's website. Be concise.

Company: {company_name}
Title: {website_data.get('title', 'None')}
Meta description: {website_data.get('meta_description', 'None')}
Social links found: {json.dumps(website_data.get('social_links', {}))}

Page content (excerpt):
{website_data.get('text_content', '')[:2000]}

Rate:
1. website_quality (1-10): 1=broken/terrible, 5=mediocre template, 10=modern/professional
2. seo_quality (1-10): based on title tag, meta description, content structure
3. notes: 1-2 sentences on what's bad/missing (be specific)

Return JSON only:
{{"website_quality": N, "seo_quality": N, "notes": "..."}}"""

    result = call_claude_json(prompt, max_tokens=500)
    if result:
        result["has_chatbot"] = website_data.get("has_chatbot", False)
        result["has_booking"] = website_data.get("has_booking", False)
        result["social_links"] = website_data.get("social_links", {})
    return result


# ── Scoring Rubric ─────────────────────────────────────────────────────────

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


def parse_date(date_str):
    """Try to parse a date string. Returns datetime or None."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str[:19], fmt)
        except ValueError:
            continue
    return None


def months_since(date_str):
    """Return months since a date string, or None if unparsable."""
    dt = parse_date(date_str)
    if dt:
        return (datetime.now() - dt).days / 30
    return None


def calculate_lead_score(data):
    """100-point deterministic scoring. Returns (score, tier, breakdown)."""
    score = 0
    breakdown = {}

    # ── 1. WEBSITE NEED (25 pts) ──
    wpts = 0
    if data.get("website_down"):
        wpts = 25
    else:
        wq = data.get("website_quality", 5)
        seo = data.get("seo_quality", 5)
        if wq <= 3:
            wpts += 20
        elif wq <= 6:
            wpts += 12
        else:
            wpts += 3
        if seo <= 3:
            wpts += 5
        elif seo <= 6:
            wpts += 2
    score += wpts
    breakdown["website"] = wpts

    # ── 2. SOCIAL MEDIA GAP (20 pts) ──
    spts = 0

    # Instagram (max 8)
    ig = data.get("instagram_handle", "")
    ig_months = months_since(data.get("instagram_last_post", ""))
    if not ig:
        spts += 8
    elif ig_months is not None and ig_months > 3:
        spts += 6
    elif ig_months is not None:
        spts += 2
    else:
        spts += 4  # exists but no post data

    # LinkedIn (max 7)
    li_months = months_since(data.get("linkedin_last_post", ""))
    if li_months is None:
        spts += 7  # no data = assume inactive
    elif li_months > 6:
        spts += 7
    elif li_months > 2:
        spts += 3

    # Facebook (max 5)
    if not data.get("facebook_present"):
        spts += 5
    else:
        spts += 1

    score += spts
    breakdown["social"] = spts

    # ── 3. CHATBOT & BOOKING GAP (15 pts) ──
    cpts = 0
    if not data.get("has_chatbot"):
        cpts += 10
    if not data.get("has_online_booking"):
        cpts += 5
    score += cpts
    breakdown["chatbot"] = cpts

    # ── 4. DECISION MAKER (15 pts) ──
    rpts = 2
    title = data.get("job_title", "").lower()
    if any(t in title for t in ["owner", "president", "ceo", "founder", "principal"]):
        rpts = 15
    elif any(t in title for t in ["vp", "vice president", "director", "partner"]):
        rpts = 10
    elif any(t in title for t in ["manager", "general manager", "gm", "operations"]):
        rpts = 5
    score += rpts
    breakdown["role"] = rpts

    # ── 5. COMPANY SIZE SWEET SPOT (15 pts) ──
    emp = data.get("employee_count", 0)
    if isinstance(emp, str):
        try:
            emp = int(re.sub(r"[^\d]", "", emp)) if emp else 0
        except ValueError:
            emp = 0
    if 5 <= emp <= 20:
        zpts = 15
    elif 21 <= emp <= 50:
        zpts = 12
    elif 51 <= emp <= 100:
        zpts = 8
    elif 101 <= emp <= 200:
        zpts = 4
    elif emp > 200:
        zpts = 2
    elif 1 <= emp <= 4:
        zpts = 8
    else:
        zpts = 8  # unknown
    score += zpts
    breakdown["size"] = zpts

    # ── 6. LOCATION (10 pts) ──
    country = data.get("country", "").lower()
    state = data.get("state", "").upper()
    if country in ("united states", "us", "usa") or state in US_STATES:
        lpts = 10
    elif country in ("canada", "ca"):
        lpts = 7
    elif country in ("uk", "united kingdom", "ireland", "australia"):
        lpts = 4
    else:
        lpts = 1
    score += lpts
    breakdown["location"] = lpts

    # ── Tier ──
    if score >= 70:
        tier = "hot"
    elif score >= 40:
        tier = "warm"
    else:
        tier = "cold"

    return score, tier, breakdown


# ── Phase 2 Orchestration ──────────────────────────────────────────────────

def enrich_single_lead(row_num, row, headers):
    """Scrape website + extract signals for a single lead (threaded)."""
    company_name = get_col_val(row, headers, ["company_name", "business_name", "name"])
    website = get_col_val(
        row, headers, ["website", "company_domain", "domain", "url"]
    )
    linkedin_url = get_col_val(
        row, headers, ["company_linkedin", "linkedin_url", "linkedin"]
    )
    city = get_col_val(row, headers, ["city"])
    state = get_col_val(row, headers, ["state"])
    country = get_col_val(row, headers, ["country"])
    job_title = get_col_val(row, headers, ["job_title", "title", "position"])
    emp_count = get_col_val(
        row,
        headers,
        ["company_employee_count", "employee_count", "employees"],
    )

    result = {"row_num": row_num, "company_name": company_name}
    for col in PHASE2_COLUMNS:
        result[col] = ""

    print(f"[Row {row_num}] Enriching: {company_name}")

    # ── 2a: Scrape website ──
    website_analysis = None
    website_data = None
    if website:
        print(f"  [Row {row_num}] Scraping: {website}")
        website_data = scrape_website_simple(website)

        if website_data:
            website_analysis = analyze_website_quality(website_data, company_name)
            if website_analysis:
                result["has_chatbot"] = (
                    "yes" if website_analysis.get("has_chatbot") else "no"
                )
                result["has_online_booking"] = (
                    "yes" if website_analysis.get("has_booking") else "no"
                )
                result["website_quality_notes"] = website_analysis.get("notes", "")
    else:
        result["website_quality_notes"] = "No website URL available"

    # ── 2c: Find Instagram from website ──
    ig_handle = None
    if website_data and website_data.get("social_links", {}).get("instagram"):
        ig_handle = website_data["social_links"]["instagram"]

    if ig_handle:
        result["instagram_handle"] = f"@{ig_handle}"

    # ── Collect scoring data (LinkedIn + Instagram added later in batch) ──
    scoring = {
        "website_quality": (
            website_analysis.get("website_quality", 5) if website_analysis else 5
        ),
        "seo_quality": (
            website_analysis.get("seo_quality", 5) if website_analysis else 5
        ),
        "website_down": (
            website_data is not None and website_data.get("status") == 0
        ),
        "has_chatbot": (
            website_analysis.get("has_chatbot", False) if website_analysis else False
        ),
        "has_online_booking": (
            website_analysis.get("has_booking", False) if website_analysis else False
        ),
        "instagram_handle": ig_handle or "",
        "instagram_last_post": "",
        "linkedin_last_post": "",
        "facebook_present": bool(
            website_data and website_data.get("social_links", {}).get("facebook")
        ),
        "job_title": job_title,
        "employee_count": emp_count,
        "country": country,
        "state": state,
    }

    result["_scoring_data"] = scoring
    result["_linkedin_url"] = linkedin_url
    result["_instagram_handle"] = ig_handle

    return result


def run_phase2(worksheet, headers, rows, dry_run=False, workers=3):
    """Phase 2: Enrich qualified leads and score them."""
    print(f"\n{'='*60}")
    print("PHASE 2: ENRICH & SCORE")
    print(f"{'='*60}")

    if not dry_run:
        headers = ensure_columns(worksheet, headers, PHASE2_COLUMNS)

    # Filter to qualified-only, skip already scored
    qualified_rows = []
    for row_num, row in rows:
        is_q = get_col_val(row, headers, ["is_qualified_hvac"])
        if is_q.lower() != "yes":
            continue
        existing = get_col_val(row, headers, ["lead_score"])
        if existing:
            print(f"  [Row {row_num}] Already scored, skipping")
            continue
        qualified_rows.append((row_num, row))

    print(f"Qualified leads to enrich: {len(qualified_rows)}\n")
    if not qualified_rows:
        print("No qualified leads to process.")
        return headers

    # ── Step 2a+2c: Scrape websites & find social handles (parallel) ──
    print("STEP 2a+2c: Scraping websites & finding social handles...\n")
    all_results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(enrich_single_lead, rn, row, headers): rn
            for rn, row in qualified_rows
        }
        for future in as_completed(futures):
            row_num = futures[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"  [Row {row_num}] Error: {e}")
                result = {"row_num": row_num, "_scoring_data": {}, "_linkedin_url": "", "_instagram_handle": ""}
                for col in PHASE2_COLUMNS:
                    result[col] = ""
                all_results.append(result)

    # Sort by row number for consistent output
    all_results.sort(key=lambda r: r["row_num"])

    # ── Step 2b: Batch fetch LinkedIn profiles ──
    print(f"\nSTEP 2b: Fetching LinkedIn profiles...")
    li_url_map = {}  # row_num -> url
    for r in all_results:
        li = r.get("_linkedin_url", "")
        if li:
            li_url_map[r["row_num"]] = li.rstrip("/")

    linkedin_data = {}
    if li_url_map:
        unique_urls = list(set(li_url_map.values()))
        linkedin_data = fetch_linkedin_profiles(unique_urls)
    else:
        print("  No LinkedIn URLs to fetch")

    # ── Step 2d: Batch fetch Instagram profiles ──
    print(f"\nSTEP 2d: Fetching Instagram profiles...")
    ig_url_map = {}  # row_num -> url
    for r in all_results:
        ig = r.get("_instagram_handle", "")
        if ig:
            ig_url = f"https://www.instagram.com/{ig}"
            ig_url_map[r["row_num"]] = ig_url

    instagram_data = {}
    if ig_url_map:
        unique_urls = list(set(ig_url_map.values()))
        instagram_data = fetch_instagram_profiles(unique_urls)
    else:
        print("  No Instagram handles to fetch")

    # ── Step 2e: Merge data + score ──
    print(f"\nSTEP 2e: Scoring {len(all_results)} leads...\n")

    for result in all_results:
        row_num = result["row_num"]
        scoring = result.get("_scoring_data", {})

        # Merge LinkedIn data
        li_url = li_url_map.get(row_num, "")
        if li_url and li_url in linkedin_data:
            li = linkedin_data[li_url]
            result["linkedin_followers"] = str(
                li.get("followers_count", li.get("follower_count", ""))
            )
            posts = li.get("posts", li.get("updates", []))
            if posts and isinstance(posts, list) and len(posts) > 0:
                p = posts[0]
                pd = p.get("date", p.get("posted_at", p.get("published_date", "")))
                if pd:
                    result["linkedin_last_post"] = str(pd)[:10]
                    scoring["linkedin_last_post"] = str(pd)[:10]

        # Merge Instagram data
        ig_url = ig_url_map.get(row_num, "")
        if ig_url and ig_url in instagram_data:
            ig = instagram_data[ig_url]
            result["instagram_followers"] = str(
                ig.get("followers", ig.get("follower_count", ""))
            )
            posts = ig.get("posts", ig.get("recent_posts", []))
            if posts and isinstance(posts, list) and len(posts) > 0:
                p = posts[0]
                pd = p.get("timestamp", p.get("date", p.get("taken_at", "")))
                if pd:
                    result["instagram_last_post"] = str(pd)[:10]
                    scoring["instagram_last_post"] = str(pd)[:10]

        # Social media notes
        notes = []
        if not result.get("instagram_handle"):
            notes.append("No Instagram")
        elif result.get("instagram_last_post"):
            notes.append(f"IG last post: {result['instagram_last_post']}")
        if not result.get("linkedin_followers"):
            notes.append("No LinkedIn data")
        elif result.get("linkedin_last_post"):
            notes.append(f"LI last post: {result['linkedin_last_post']}")
        if scoring.get("facebook_present"):
            notes.append("Has Facebook")
        else:
            notes.append("No Facebook")
        result["social_media_notes"] = "; ".join(notes)

        # Score
        total, tier, bd = calculate_lead_score(scoring)
        result["lead_score"] = str(total)
        result["lead_tier"] = tier
        result["score_breakdown"] = ", ".join(f"{k}:{v}" for k, v in bd.items())

        company = result.get("company_name", "Unknown")
        print(
            f"  [Row {row_num}] {company} -> {total} ({tier.upper()}) "
            f"| {result['score_breakdown']}"
        )

    # Batch write all Phase 2 results to sheet
    print(f"\n  Writing {len(all_results)} scored leads to sheet...")
    pending = [(r["row_num"], r) for r in all_results]
    batch_update_rows(worksheet, headers, pending, PHASE2_COLUMNS, dry_run)

    # ── Summary ──
    tiers = {"hot": 0, "warm": 0, "cold": 0}
    scores = []
    for r in all_results:
        t = r.get("lead_tier", "cold")
        tiers[t] = tiers.get(t, 0) + 1
        try:
            scores.append(int(r.get("lead_score", 0)))
        except (ValueError, TypeError):
            pass

    print(f"\n{'='*60}")
    print("PHASE 2 COMPLETE")
    print(f"{'='*60}")
    print(f"Leads scored: {len(all_results)}")
    print(f"  HOT  (70-100): {tiers.get('hot', 0)}")
    print(f"  WARM (40-69):  {tiers.get('warm', 0)}")
    print(f"  COLD (1-39):   {tiers.get('cold', 0)}")
    if scores:
        print(f"  Average score: {sum(scores) / len(scores):.1f}")
    if dry_run:
        print("[DRY RUN] No changes written to sheet")

    # Save results to .tmp/
    os.makedirs(".tmp", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f".tmp/lead_scores_{ts}.json"
    serializable = []
    for r in all_results:
        s = {k: v for k, v in r.items() if not k.startswith("_")}
        serializable.append(s)
    with open(out_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to: {out_path}")

    return headers


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Qualify & Rank HVAC Leads — Phase 1 (qualify) + Phase 2 (enrich & score)"
    )
    parser.add_argument(
        "--sheet_url", required=True, help="Google Sheet URL with leads"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["1", "2", "both"],
        help="Phase to run: 1 (qualify), 2 (enrich+score), both",
    )
    parser.add_argument("--worksheet", help="Worksheet name (default: first sheet)")
    parser.add_argument(
        "--start_row", type=int, help="Starting data row (2 = first data row)"
    )
    parser.add_argument("--end_row", type=int, help="Ending row (inclusive)")
    parser.add_argument(
        "--workers", type=int, default=3, help="Parallel workers for Phase 2 (default: 3)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Preview without writing to sheet",
    )

    args = parser.parse_args()
    start_time = time.time()

    print("Connecting to Google Sheet...")
    worksheet, headers, rows = read_leads(
        args.sheet_url,
        worksheet_name=args.worksheet,
        start_row=args.start_row,
        end_row=args.end_row,
    )
    print(f"Read {len(rows)} rows, {len(headers)} columns\n")

    if args.phase in ("1", "both"):
        headers, _ = run_phase1(worksheet, headers, rows, dry_run=args.dry_run)

        if args.phase == "both":
            # Re-read to get updated qualification flags
            print("\nRe-reading sheet for Phase 2...")
            _, headers, rows = read_leads(
                args.sheet_url,
                worksheet_name=args.worksheet,
                start_row=args.start_row,
                end_row=args.end_row,
            )

    if args.phase in ("2", "both"):
        run_phase2(
            worksheet, headers, rows, dry_run=args.dry_run, workers=args.workers
        )

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
