#!/usr/bin/env python3
"""
Upwork Job Scraper using Bright Data MCP

Scrapes Upwork search results via Bright Data's MCP server (scrape_as_markdown).
Parses markdown output to extract structured job listings.

Usage:
    python execution/upwork_brightdata_scraper.py --keywords "ai agent,n8n,voice ai" --days 1
    python execution/upwork_brightdata_scraper.py --keyword "automation" -o .tmp/upwork_jobs.json
"""

import os
import re
import json
import time
import argparse
import requests
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

BRIGHTDATA_API_TOKEN = os.environ.get("BRIGHTDATA_API_TOKEN")
MCP_BASE = "https://mcp.brightdata.com"
UPWORK_SEARCH_URL = "https://www.upwork.com/nx/search/jobs/"


def mcp_scrape(url: str, timeout_secs: int = 180) -> str:
    """Scrape a URL via Bright Data MCP server. Returns markdown string.

    Uses a subprocess with a temp script file to handle SSE reliably.
    """
    if not BRIGHTDATA_API_TOKEN:
        raise ValueError("BRIGHTDATA_API_TOKEN not found in environment")

    import subprocess
    import tempfile

    # Write helper script to a temp file (avoids f-string escaping issues)
    script_content = _MCP_HELPER_SCRIPT.replace("__TOKEN__", BRIGHTDATA_API_TOKEN)
    script_content = script_content.replace("__BASE__", MCP_BASE)
    script_content = script_content.replace("__TARGET__", url)
    script_content = script_content.replace("__TIMEOUT__", str(timeout_secs))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        script_path = f.name

    try:
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=timeout_secs + 30,
        )

        if result.returncode == 0 and result.stdout:
            return result.stdout
        elif result.returncode == 1:
            raise Exception("Failed to establish MCP session")
        elif result.returncode == 2:
            raise Exception(f"MCP scrape timed out after {timeout_secs}s")
        else:
            raise Exception(f"MCP scrape failed: exit={result.returncode}, stderr={result.stderr[:200]}")
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


# Helper script template — runs in subprocess, no f-string escaping needed
_MCP_HELPER_SCRIPT = r'''
import requests, json, time, sys, os, threading

TOKEN = "__TOKEN__"
BASE = "__BASE__"
TARGET = "__TARGET__"
TIMEOUT = int("__TIMEOUT__")

session_id = None
responses = []

def sse_listen():
    global session_id
    try:
        r = requests.get(f"{BASE}/sse?token={TOKEN}", stream=True, timeout=TIMEOUT + 30)
        buf = ""
        for chunk in r.iter_content(chunk_size=4096, decode_unicode=True):
            buf += chunk
            while "\n\n" in buf:
                event_str, buf = buf.split("\n\n", 1)
                data_lines = []
                for line in event_str.split("\n"):
                    if line.startswith("data: "):
                        data_lines.append(line[6:])
                    elif line.startswith("data:"):
                        data_lines.append(line[5:])
                if data_lines:
                    data = "\n".join(data_lines)
                    if data.startswith("/messages"):
                        session_id = data.split("sessionId=")[1]
                    else:
                        responses.append(data)
    except Exception:
        pass

t = threading.Thread(target=sse_listen, daemon=True)
t.start()

for _ in range(20):
    if session_id:
        break
    time.sleep(0.5)

if not session_id:
    os._exit(1)

msg_url = f"{BASE}/messages?sessionId={session_id}"
payload = {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"scrape_as_markdown","arguments":{"url":TARGET}}}
resp = requests.post(msg_url, json=payload, timeout=30)

for _ in range(TIMEOUT // 2):
    time.sleep(2)
    for resp in list(responses):
        try:
            d = json.loads(resp)
            if "result" in d:
                content = d["result"].get("content", [])
                if content:
                    text = content[0].get("text", "")
                    if text:
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        os._exit(0)
        except Exception:
            pass

os._exit(2)
'''


def parse_time_ago(time_str: str) -> str:
    """Convert 'Posted X minutes/hours/days ago' to ISO timestamp estimate."""
    now = datetime.now(timezone.utc)
    time_str = time_str.lower().strip()

    match = re.search(r"(\d+)\s*(minute|hour|day|week|month)", time_str)
    if not match:
        return now.isoformat()

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "minute":
        delta = timedelta(minutes=amount)
    elif unit == "hour":
        delta = timedelta(hours=amount)
    elif unit == "day":
        delta = timedelta(days=amount)
    elif unit == "week":
        delta = timedelta(weeks=amount)
    elif unit == "month":
        delta = timedelta(days=amount * 30)
    else:
        delta = timedelta()

    return (now - delta).isoformat()


def extract_job_id_from_url(url_path: str) -> str:
    """Extract job ID from Upwork URL path like /jobs/Title_~0123456789/"""
    match = re.search(r"~(\w+)", url_path)
    if match:
        return f"~{match.group(1)}"
    return ""


def parse_budget(budget_line: str) -> tuple:
    """Parse budget string. Returns (budget_str, budget_raw)."""
    if not budget_line:
        return "Not specified", {}

    # Fixed price: "Est. budget: $500.00"
    fixed_match = re.search(r"\$[\d,]+(?:\.\d+)?", budget_line)
    if fixed_match and "budget" in budget_line.lower():
        amount = float(fixed_match.group().replace("$", "").replace(",", ""))
        return f"${amount:,.0f} fixed", {"fixedBudget": amount}

    # Hourly: "$25.00 - $50.00" or "$30.00/hr"
    hourly_match = re.findall(r"\$([\d,]+(?:\.\d+)?)", budget_line)
    if hourly_match and ("hr" in budget_line.lower() or "hourly" in budget_line.lower()):
        rates = [float(r.replace(",", "")) for r in hourly_match]
        if len(rates) >= 2:
            return f"${rates[0]}-${rates[1]}/hr", {"hourlyRate": {"min": rates[0], "max": rates[1]}}
        elif rates:
            return f"${rates[0]}/hr", {"hourlyRate": {"min": rates[0], "max": rates[0]}}

    # Just a dollar amount
    if fixed_match:
        amount = float(fixed_match.group().replace("$", "").replace(",", ""))
        return f"${amount:,.0f}", {"fixedBudget": amount}

    return budget_line, {}


def parse_markdown_jobs(markdown: str, keyword: str = "") -> list:
    """Parse Upwork job listings from markdown scraped content."""
    jobs = []

    # Split into job blocks starting with "Posted"
    blocks = re.split(r"(?=Posted \d+\s+(?:minute|hour|day|week|month))", markdown)
    job_blocks = [b for b in blocks if b.startswith("Posted")]

    for block in job_blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) < 3:
            continue

        # Line 0: Posted time
        posted_line = lines[0]
        posted = parse_time_ago(posted_line)

        # Line 1: Title with link [Title](URL)
        title_match = re.match(r"\[(.+?)\]\((.+?)\)", lines[1]) if len(lines) > 1 else None
        if not title_match:
            continue

        title = title_match.group(1)
        url_path = title_match.group(2)
        job_id = extract_job_id_from_url(url_path)

        # Build full URL
        if url_path.startswith("/"):
            # Clean up URL path (remove referrer params)
            clean_path = url_path.split("?")[0]
            url = f"https://www.upwork.com{clean_path}"
        else:
            url = url_path

        # Parse remaining lines for metadata
        job_type = ""
        experience = ""
        budget_str = "Not specified"
        budget_raw = {}
        description = ""
        skills = []
        proposals_text = ""

        # Lines 2+: parse type, experience, budget, description, skills
        desc_started = False
        for line in lines[2:]:
            line_lower = line.lower()

            # Job type
            if line_lower in ("fixed price", "fixed-price", "hourly"):
                job_type = line
                continue

            # Experience level
            if line_lower in ("entry level", "intermediate", "expert"):
                experience = line
                continue

            # Budget
            if line_lower.startswith("est. budget") or line_lower.startswith("est.budget"):
                budget_str, budget_raw = parse_budget(line)
                continue

            # Hourly range (e.g., "$25.00 - $50.00")
            if re.match(r"^\$[\d,]+.*-.*\$[\d,]+", line):
                budget_str, budget_raw = parse_budget(line + " hourly")
                continue

            # Proposals count
            if "proposal" in line_lower:
                prop_match = re.search(r"(\d+)\s*to\s*(\d+)|less\s*than\s*(\d+)|(\d+)\+", line_lower)
                if prop_match:
                    proposals_text = line
                continue

            # Payment verified / client info lines (skip)
            if any(x in line_lower for x in ["payment verified", "rating", "$", "spent"]):
                if not desc_started:
                    continue

            # Skills are typically short (1-4 words), no periods
            if len(line) < 50 and "." not in line and not desc_started:
                # Could be a skill or could be description start
                # Skills come AFTER description in Upwork markdown
                pass

            # If we haven't found the description yet and this is a long line, it's the description
            if not description and len(line) > 80:
                description = line
                desc_started = True
                continue

            # After description, remaining short lines are skills
            if description and len(line) < 60 and not any(
                x in line_lower for x in ["posted", "proposal", "payment", "less than"]
            ):
                skills.append(line)

        # Parse proposals count
        proposals_count = 0
        if proposals_text:
            nums = re.findall(r"\d+", proposals_text)
            if nums:
                proposals_count = max(int(n) for n in nums)

        # Build job dict matching the pipeline's expected format
        job = {
            "id": job_id,
            "title": title,
            "description": description,
            "url": url,
            "budget": budget_str,
            "budget_raw": budget_raw,
            "category": "",
            "experience_level": experience,
            "skills": skills[:10],
            "posted": posted,
            "connects_cost": 0,
            "client": {
                "country": "",
                "timezone": "",
                "payment_verified": False,
                "total_spent": 0,
                "total_hires": 0,
                "hire_rate": 0,
                "feedback_score": 0,
            },
            "is_featured": False,
            "proposals_count": proposals_count,
            "keyword": keyword,
        }

        jobs.append(job)

    return jobs


def scrape_keyword(keyword: str, days: int = 1, per_page: int = 50) -> list:
    """Scrape Upwork search results for a single keyword via MCP."""
    encoded = quote_plus(keyword)
    url = f"{UPWORK_SEARCH_URL}?q={encoded}&sort=recency&per_page={per_page}"

    print(f"  Scraping: '{keyword}' via Bright Data MCP...")
    try:
        markdown = mcp_scrape(url)
    except Exception as e:
        print(f"  Failed to fetch '{keyword}': {e}")
        return []

    if not markdown or len(markdown) < 500:
        print(f"  Empty or too short response for '{keyword}' ({len(markdown) if markdown else 0} chars)")
        print(f"  Response preview: {repr(markdown[:200]) if markdown else 'None'}")
        return []

    jobs = parse_markdown_jobs(markdown, keyword=keyword)
    print(f"  Found {len(jobs)} jobs for '{keyword}'")

    # Filter by date if days specified
    if days and jobs:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filtered = []
        for job in jobs:
            if job["posted"]:
                try:
                    posted_dt = datetime.fromisoformat(job["posted"])
                    if posted_dt >= cutoff:
                        filtered.append(job)
                except (ValueError, TypeError):
                    filtered.append(job)
            else:
                filtered.append(job)
        if len(filtered) != len(jobs):
            print(f"  {len(filtered)} jobs within last {days} day(s)")
        return filtered

    return jobs


def scrape_keywords(keywords: list, days: int = 1, per_page: int = 50) -> list:
    """Scrape Upwork for multiple keywords, union results, deduplicate by job ID."""
    all_jobs = []
    seen_ids = set()

    for keyword in keywords:
        jobs = scrape_keyword(keyword, days=days, per_page=per_page)
        for job in jobs:
            job_id = job.get("id", "")
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                all_jobs.append(job)
            elif not job_id:
                all_jobs.append(job)

        # Delay between keywords to avoid rate limiting
        if keyword != keywords[-1]:
            time.sleep(2)

    print(f"\nTotal: {len(all_jobs)} unique jobs across {len(keywords)} keywords")
    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Scrape Upwork jobs via Bright Data MCP")

    parser.add_argument("--keyword", "-k", help="Single keyword to search")
    parser.add_argument(
        "--keywords", help="Comma-separated keywords (e.g., 'ai agent,n8n,voice ai')"
    )
    parser.add_argument(
        "--days", "-d", type=int, default=1, help="Only jobs from last N days (default: 1)"
    )
    parser.add_argument(
        "--per-page", type=int, default=50, help="Results per page (default: 50)"
    )
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    elif args.keyword:
        keywords = [args.keyword]
    else:
        print("Error: provide --keyword or --keywords")
        return

    print(f"Scraping Upwork via Bright Data MCP")
    print(f"Keywords: {keywords}")
    print(f"Days: {args.days}")
    print()

    jobs = scrape_keywords(keywords, days=args.days, per_page=args.per_page)

    # Display results
    print(f"\n=== {len(jobs)} jobs found ===\n")
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job['title'][:70]}")
        print(
            f"   Budget: {job['budget']} | Level: {job['experience_level']} | "
            f"Proposals: ~{job.get('proposals_count', '?')}"
        )
        print(f"   Skills: {', '.join(job['skills'][:5])}")
        print(f"   Keyword: {job.get('keyword', '')}")
        print()

    if len(jobs) > 10:
        print(f"... and {len(jobs) - 10} more jobs")

    # Save output
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(jobs, f, indent=2)
        print(f"\nSaved {len(jobs)} jobs to {args.output}")

    return jobs


if __name__ == "__main__":
    main()
