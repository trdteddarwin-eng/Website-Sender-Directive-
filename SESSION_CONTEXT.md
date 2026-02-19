# TedCA Pipeline Dashboard — Full System Overview

Use this document to onboard a new Claude session. It covers everything built, how it works, what's been fixed, and where things stand.

---

## What This System Does

TedCA is an automated HVAC lead outreach pipeline. It takes raw leads from a Google Sheet, researches each company, generates a custom "spec website" for them, deploys it to Netlify, drafts personalized outreach emails with before/after screenshots, and manages a 4-touch email sequence — all from a single Flask dashboard.

**The flow for each lead:**
1. **Research** — Scrape their website + Google reviews, run AI analysis (pain points, ROI estimate)
2. **Design** — Generate a full custom HTML spec site via Claude (through OpenRouter API)
3. **Judge** — Screenshot the new site, run quality checks (score 0-100)
4. **Ops** — Deploy to Netlify, generate personalized outreach email + 3 follow-ups, create Gmail drafts

---

## Architecture: 3-Layer System

**Layer 1: Directives** (`directives/`) — SOPs written in Markdown. Define goals, inputs, tools, outputs.

**Layer 2: Orchestration** — Claude (you). Read directives, call execution tools, handle errors, update directives with learnings.

**Layer 3: Execution** (`execution/`) — 80+ deterministic Python scripts. API calls, scraping, file ops. Reliable and testable.

**Why:** LLMs are probabilistic. Business logic needs determinism. The 3-layer split means Claude only handles decision-making; everything else is pushed into tested Python scripts.

---

## Key Directories

```
/Users/yoljean/Downloads/Ted Workspace/
├── CLAUDE.md                 # Agent instructions (read this first — it's the system bible)
├── SESSION_CONTEXT.md        # This file
├── .env                      # API keys (OPENROUTER_API_KEY, NETLIFY_AUTH_TOKEN, ANTHROPIC_API_KEY, KIE_API_KEY)
├── token.json                # Google OAuth token (Sheets + Drive)
├── credentials.json          # Google OAuth client credentials
├── gmail_token.json          # Gmail OAuth token
├── gmail_credentials.json    # Gmail OAuth client credentials
├── directives/               # SOPs (spec_site_pipeline.md is the main one)
├── execution/                # Python scripts (80+)
├── pipeline-app/             # Flask web dashboard
│   ├── app.py                # Entry point — python3 pipeline-app/app.py (port 5050)
│   ├── config.py             # Loads .env, defines paths, Google Sheet ID
│   ├── services/
│   │   ├── supabase_client.py  # DATA LAYER (misleading name — actually reads Google Sheets + local JSON)
│   │   ├── pipeline_runner.py  # Orchestrates the 4-phase pipeline in a background thread
│   │   ├── email_service.py    # Gmail API integration
│   │   ├── lead_importer.py    # Import leads from JSON files into Google Sheets
│   │   ├── reply_checker.py    # Polls Gmail threads for replies to sent emails
│   │   ├── sequence_scheduler.py # APScheduler: reply checks every 5min, follow-up checks every 1hr
│   │   └── sse_manager.py      # Server-Sent Events broadcaster for live pipeline updates
│   ├── blueprints/             # Flask route handlers
│   │   ├── dashboard.py        # GET / — KPIs, activity feed
│   │   ├── leads.py            # GET /leads, GET /leads/<slug> — lead list + detail
│   │   ├── pipeline.py         # GET /pipeline — live agent monitor with SSE
│   │   ├── sequences.py        # GET /sequences — email sequence manager
│   │   ├── analytics.py        # GET /analytics — charts and stats
│   │   ├── settings.py         # GET /settings — connection status, API keys
│   │   └── api.py              # All JSON API endpoints (/api/pipeline/run, /api/leads/import, etc.)
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS + JS
└── .tmp/                       # All intermediate files (scraped data, generated sites, screenshots)
    ├── pipeline-data/          # Local JSON storage for operational data
    │   ├── pipeline_runs.json
    │   ├── emails.json
    │   ├── email_sequences.json
    │   ├── spec_sites.json
    │   ├── replies.json
    │   └── activity_log.json
    └── {slug}/                 # Per-lead working directory
        ├── website_data.json
        ├── reviews_data.json
        ├── analysis.json
        ├── research.json
        ├── index.html          # Generated spec site
        ├── old-site.png/jpg    # Screenshot of their current website
        ├── new-site.png/jpg    # Screenshot of the generated spec site
        ├── deploy-info.json    # Netlify deploy URL
        ├── outreach-email.html # First touch email HTML
        ├── email-meta.json     # Subject, to, attachments
        └── followup-touch{2,3,4}.html + meta
```

---

## Data Layer (IMPORTANT)

**The file is called `supabase_client.py` but it does NOT use Supabase.** We replaced Supabase with:

- **Leads** → Google Sheets (read via `gspread`, write-back status updates to specific cells)
- **Operational data** → Local JSON files in `.tmp/pipeline-data/`

### Google Sheet
- **URL:** `https://docs.google.com/spreadsheets/d/1rmxqViBWof7Jo2yX9AEBFTATzuzF_crqh5HxG2z-1b4/edit`
- **479 leads:** 83 hot, 184 warm, 212 unscored
- **47 columns** including: first_name, last_name, email, phone, company_name, website, city, state, lead_score, lead_tier, send_status, is_qualified_hvac, score_breakdown, etc.
- **Caching:** In-memory cache with 60-second TTL. Invalidated on any write.
- **Auth:** Uses `token.json` (Google OAuth) in workspace root.

### Data Mapping
- Sheet's `send_status` → app's `pipeline_status` (""→"pending", "sent"→"emailing", etc.)
- Sheet's `is_qualified_hvac` → app's `is_qualified` ("yes"/"no" → True/False)
- Each lead gets a deterministic `id` (UUID5 from slug) and `slug` (slugified company_name)

### JSON Storage
Each JSON file is an array of objects. IDs are UUID4 strings. Thread-safe via `threading.Lock` per file. Files auto-created as empty `[]` on first access.

---

## Pipeline Runner (pipeline_runner.py)

Runs in a background daemon thread. Steps:

1. **Researcher** — `scrape_website_content.py`, `scrape_google_reviews.py`, `analyze_lead_for_roi.py`, `combine_research.py`, `screenshot_website.py`
2. **Designer** — `generate_spec_site.py` (Claude via OpenRouter, model: `anthropic/claude-sonnet-4`)
3. **Judge** — `screenshot_website.py` (new site), programmatic HTML quality score
4. **Ops** — `deploy_spec_site.py` (Netlify), `generate_outreach_email.py` (Claude Haiku), `create_gmail_draft.py`, `generate_followup_email.py`, create email sequence

Each step calls execution scripts via `subprocess.run()`. Status updates flow through:
- `supabase_client.py` → updates lead status in Google Sheets + pipeline run state in JSON
- `sse_manager.py` → broadcasts named SSE events to connected browsers

### SSE Events (Named Events)
The pipeline runner sends these via `sse.publish()`:
- `pipeline_started` — data: `{slug, lead}`
- `agent_update` — data: `{agent, status, task, slug, completed_tasks, ...}`
- `pipeline_log` — data: `{time, agent, message}`
- `pipeline_completed` — data: `{slug}`
- `pipeline_failed` — data: `{slug, error}`

The pipeline.html JS listens via `evtSource.addEventListener('event_name', ...)` — NOT `onmessage`.

---

## Key Execution Scripts

| Script | What it does |
|---|---|
| `screenshot_website.py` | Playwright headless screenshot. Uses `wait_until="load"` (not networkidle). Detects maintenance/error/login pages via page content analysis. Writes `.meta.json` sidecar with `{usable, reason}`. device_scale_factor=1 for email-appropriate sizing. |
| `generate_spec_site.py` | Full HTML spec site via OpenRouter (Claude Sonnet 4). Single API call → self-contained HTML. |
| `generate_outreach_email.py` | Personalized email via Claude Haiku. Before/after screenshots as CID attachments. Images constrained to `width="600"` with inline styles for email client compatibility. Checks `.meta.json` to skip unusable old-site screenshots. |
| `generate_followup_email.py` | Generates touches 2-4 with different angles. |
| `deploy_spec_site.py` | Deploys HTML to Netlify via API. |
| `create_gmail_draft.py` | Creates Gmail draft with HTML body + CID image attachments. |
| `scrape_website_content.py` | Scrapes up to 5 pages of a website for content analysis. |
| `scrape_google_reviews.py` | Scrapes Google Maps reviews for a business. |
| `read_sheet.py` | Standalone Google Sheets reader (used for testing/one-off reads). |
| `qualify_and_rank_leads.py` | AI-powered lead scoring and qualification. |
| `send_gmail_api.py` | Sends Gmail drafts via API. |

---

## What Was Built/Fixed in This Session

### 1. Replaced Supabase with Google Sheets + Local JSON
- **7 files modified:** config.py, supabase_client.py (full rewrite), lead_importer.py, settings.py, api.py, settings.html, requirements.txt
- Removed `supabase` dependency, added `gspread`
- All 30+ data functions keep identical signatures — blueprints unchanged
- Added `get_email_by_id()` function to replace direct Supabase client calls in api.py

### 2. Fixed Pipeline SSE Live Updates
- **Bug:** pipeline.html used `onmessage` which only catches unnamed SSE events. The SSE manager sends named events (`event: agent_update`). UI never received updates.
- **Fix:** Replaced with `addEventListener` for each named event type (`pipeline_started`, `agent_update`, `pipeline_log`, `pipeline_completed`, `pipeline_failed`)
- **Added hydration:** On page load, fetches `/api/pipeline/status` and populates agent cards + log from existing run state

### 3. Fixed Screenshot Issues
- **`device_scale_factor`:** Reduced from 2 to 1 (2880px → 1440px). Email images don't need retina resolution.
- **`wait_until`:** Changed from `"networkidle"` to `"load"` with fallback to `"domcontentloaded"`. Networkidle hangs on sites with persistent connections.
- **Page content detection:** After capture, checks for maintenance pages, login walls, error pages (404/503), parked domains. Writes `.meta.json` sidecar.
- **Email image sizing:** Added `width="600" style="display:block;max-width:100%;width:600px;height:auto;"` inline on all `<img>` tags. Works even when email clients strip `<style>` blocks.
- **Unusable screenshot skipping:** Pipeline runner and email generator both check `.meta.json` before including old-site screenshots. Maintenance/error pages are excluded from emails.

---

## How to Run

```bash
cd "/Users/yoljean/Downloads/Ted Workspace/pipeline-app"
python3 app.py
# → http://localhost:5050
```

**Prerequisites:**
- `token.json` in workspace root (Google OAuth — run `execution/read_sheet.py` to authenticate)
- `gmail_token.json` + `gmail_credentials.json` for Gmail drafts
- `.env` with: `OPENROUTER_API_KEY`, `NETLIFY_AUTH_TOKEN`, `ANTHROPIC_API_KEY`
- Playwright browsers: `python3 -m playwright install chromium`

---

## Known Issues / TODO

1. **Pipeline run state can get orphaned** — If the app is killed while a pipeline is running, the JSON state shows "running" forever. Need a cleanup/recovery mechanism.
2. **Google Sheets rate limits** — 60 reads/min. The cache helps but heavy pipeline activity could hit limits. Consider batching write-backs.
3. **Palette rotation for spec sites** — The directive says to vary colors per lead, but it's only using modulo on completed run count. Each batch might look similar.
4. **`supabase_client.py` should be renamed** — It's confusing. Should be `data_client.py` or `db.py`. All imports reference it as `from services import supabase_client as db`.

---

## GitHub Repo

`https://github.com/trdteddarwin-eng/Website-Sender-Directive-.git`

---

## Error Log

Check `CLAUDE.md` for the full error log — it's a running list of mistakes and permanent rules. Always scan it before starting any task.
