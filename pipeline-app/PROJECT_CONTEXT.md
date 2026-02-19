# TedCA Pipeline Web App — Full Project Context

> **Purpose of this file:** This documents everything built so a new Claude session can pick up exactly where we left off. Read this file first before doing any work on this project.

## What This Is

A **local web app** (Flask + vanilla HTML/CSS/JS) that consolidates the TedCA spec site pipeline into a single dashboard. Previously, the pipeline ran manually from the terminal via Claude Code Agent Teams. This app adds: lead management, live pipeline monitoring, email sequences with semi-auto sending, reply tracking, and analytics.

**Scale:** 10 leads/day, ~3,600 leads/year.

## Tech Stack

| Layer | Tech | Notes |
|---|---|---|
| Backend | Python Flask | Single `python3 app.py` to start, runs on port 5050 |
| Frontend | Vanilla HTML/CSS/JS | No React, no npm, no build step. Jinja2 templates |
| Database | Supabase (Postgres) | Free tier 500MB — fits ~3 years of data |
| Charts | Chart.js 4 from CDN | Bar, line, doughnut, pie charts |
| Fonts | Inter + JetBrains Mono | Google Fonts CDN |
| Live updates | Server-Sent Events (SSE) | Flask-native, simpler than WebSocket |
| Background jobs | APScheduler | Reply check every 5min, follow-up check every 1hr |
| Theme | Dark | Navy `#0B1D3A` / Amber `#D4922A` brand colors |

## Current Status

### What's Done (Phase 1-6 complete)
- All 7 pages render correctly (HTTP 200 verified)
- All 22 routes registered and working
- APScheduler starts automatically
- SSE broadcasting functional
- All CRUD operations for 7 Supabase tables
- Pipeline runner orchestrates existing execution scripts via subprocess
- Gmail integration (send drafts, check replies, detect sentiment)
- Lead import from ranked JSON files
- New `execution/generate_spec_site.py` script (OpenRouter API)

### What's Pending
1. **Supabase setup** — need to create project and add `SUPABASE_URL` + `SUPABASE_KEY` to `.env`
2. **Run `schema.sql`** in Supabase SQL editor to create 7 tables
3. **Import leads** via Settings page or API
4. **End-to-end test** — run full pipeline from web UI

## File Structure (37 files)

```
pipeline-app/
├── app.py                       # Entry point. Creates Flask app, registers blueprints, starts scheduler
├── config.py                    # Loads ../.env, exports SUPABASE_URL, SUPABASE_KEY, API keys, paths, palettes
├── requirements.txt             # flask, supabase, apscheduler, requests, google-auth, etc.
├── schema.sql                   # CREATE TABLE for all 7 Supabase tables with indexes
├── PROJECT_CONTEXT.md           # This file
│
├── blueprints/
│   ├── __init__.py
│   ├── dashboard.py             # GET / — KPI cards, throughput chart, activity feed, today's follow-ups
│   ├── leads.py                 # GET /leads (filtered table), GET /leads/<slug> (detail with tabs)
│   ├── pipeline.py              # GET /pipeline (agent monitor), GET /api/pipeline/stream (SSE)
│   ├── sequences.py             # GET /sequences — today's sends, calendar, all sequences table
│   ├── analytics.py             # GET /analytics — funnel, email perf, sentiment, throughput
│   ├── settings.py              # GET /settings — connection tests, API keys, import, DB setup
│   └── api.py                   # 15 JSON API endpoints (see API section below)
│
├── services/
│   ├── __init__.py
│   ├── supabase_client.py       # Full CRUD for all 7 tables + aggregate queries
│   ├── pipeline_runner.py       # PipelineRunner class — runs 4 agents via subprocess, updates Supabase + SSE
│   ├── email_service.py         # Gmail OAuth wrapper — send_draft(), get_thread_messages(), check_gmail_auth()
│   ├── reply_checker.py         # Polls Gmail threads for replies, detects sentiment, stops sequences
│   ├── sequence_scheduler.py    # APScheduler init — 5min reply check, 1hr followup check
│   ├── lead_importer.py         # Imports ranked JSON → Supabase (slugify, upsert, dedup)
│   └── sse_manager.py           # SSEManager singleton — subscribe/unsubscribe/publish/stream
│
├── templates/
│   ├── base.html                # Layout: sidebar nav (6 links), toast container, modal overlay, app.js include
│   ├── dashboard.html           # 4 KPIs, Chart.js throughput bar chart, today's follow-ups, activity feed
│   ├── leads.html               # Toolbar (tier/status/search filters), sortable table, pagination
│   ├── lead_detail.html         # 4 tabs: Research | Spec Site (iframe) | Emails (table) | Timeline
│   ├── pipeline.html            # Run buttons, 4 agent cards with timers, log panel, preview iframe, queue
│   ├── sequences.html           # Today's sends (preview/send), upcoming calendar, all sequences table
│   ├── analytics.html           # 5 KPIs + 4 Chart.js charts (funnel, email, sentiment, throughput)
│   └── settings.html            # Connection status, API keys, test buttons, import, DB setup
│
└── static/
    ├── css/style.css            # Complete dark theme: 600+ lines, variables, cards, tables, badges, modals, etc.
    └── js/
        ├── app.js               # showToast(), openModal(), closeModal(), apiPost(), apiGet(), previewEmail(), sendEmail()
        ├── dashboard.js         # initDashboard(throughputData) — 30-day bar chart
        ├── leads.js             # Filter auto-submit, debounced search, sortLeads(), runPipelineFor()
        ├── lead_detail.js       # Tab switching, loadResearch() from API, skipEmail()
        ├── pipeline.js          # SSE EventSource, updateAgentCard(), updateTimers(), addLogEntry(), runNextLead()
        ├── sequences.js         # pauseSequence(), resumeSequence(), skipEmailInSeq()
        └── analytics.js         # initAnalytics() — funnel, email doughnut, sentiment pie, throughput line
```

## New Execution Script Created

**`execution/generate_spec_site.py`** — Generates complete spec site HTML via OpenRouter API.

- Model: `anthropic/claude-sonnet-4`
- Takes: `--research` (research.json path), `--palette_index` (0-4), `--hero_style_index` (0-3), `--output` (index.html path)
- Returns self-contained HTML (inline CSS, Google Fonts only)
- Enforces: no scroll-reveal animations, phone in 4 places, working hamburger menu, real reviews verbatim
- 5 color palettes rotate per lead, 4 hero styles rotate independently

## Supabase Schema (7 tables)

### `leads`
Primary lead data. Key fields: `slug` (UNIQUE), `first_name`, `last_name`, `email`, `phone`, `company_name`, `website`, `city`, `state`, `lead_score` INT, `lead_tier` TEXT (hot/warm/cold), `pipeline_status` TEXT (pending→researching→designing→reviewing→deploying→emailing→completed→failed), `raw_data` JSONB.

### `pipeline_runs`
Each pipeline execution. Key fields: `lead_id` FK, `slug`, `status` (running/completed/failed/cancelled), `agents` JSONB (researcher/designer/judge/ops each with status/task/completed_tasks/started_at/completed_at), `palette_index`, `hero_style_index`, `judge_score`, `log` JSONB.

### `spec_sites`
Deployed sites. Key fields: `lead_id` FK, `slug`, `deploy_url`, `deploy_id`, `judge_score`, `palette_index`, `hero_style`, `html_path`, `screenshot_path`.

### `emails`
Every email (outreach + follow-ups). Key fields: `lead_id` FK, `slug`, `touchpoint` INT (1-4), `subject`, `html_content`, `status` (draft→ready→sent→opened→replied→bounced→skipped), `gmail_draft_id`, `gmail_message_id`, `gmail_thread_id`, `scheduled_send_date` DATE, `sent_at`.

### `email_sequences`
Per-lead sequence state. Key fields: `lead_id` FK, `slug` UNIQUE, `status` (active/paused/completed/stopped_reply), `current_touchpoint` INT, `next_send_date` DATE, `spec_site_url`.

### `replies`
Detected Gmail replies. Key fields: `lead_id` FK, `email_id` FK, `gmail_message_id`, `from_email`, `body_preview` (500 chars), `body_full`, `sentiment` (positive/negative/neutral/out_of_office), `received_at`.

### `activity_log`
Timestamped events. Key fields: `lead_id` FK, `slug`, `event_type`, `event_data` JSONB, `agent`, `message`, `created_at`.

## API Endpoints (15 total)

### Pipeline
- `POST /api/pipeline/run` — Start pipeline for next HOT lead or specific `{slug}`
- `POST /api/pipeline/run-batch` — Start pipeline for N leads (max 10)
- `GET /api/pipeline/status` — Get active pipeline run status
- `GET /api/pipeline/stream` — SSE stream for live updates

### Leads
- `POST /api/leads/import` — Import from JSON file `{filepath}`
- `GET /api/leads/<slug>/research` — Get research.json for a lead

### Emails
- `POST /api/emails/<id>/send` — Send a Gmail draft, advance sequence
- `POST /api/emails/<id>/skip` — Skip a scheduled email
- `GET /api/emails/<id>/preview` — Get email HTML content for preview modal

### Sequences
- `POST /api/sequences/<id>/pause` — Pause a sequence
- `POST /api/sequences/<id>/resume` — Resume a paused sequence

### Settings
- `GET /api/settings/test-supabase` — Test Supabase connection
- `GET /api/settings/test-gmail` — Test Gmail OAuth

### Preview
- `GET /api/preview/<slug>` — Serve spec site HTML for iframe preview

## How the Pipeline Runner Works

When user clicks [Run Next Lead]:
1. Flask picks next unprocessed HOT lead (highest score)
2. Calculates palette (completed count % 5) and hero style (% 4)
3. Creates `pipeline_runs` row in Supabase
4. Spawns `PipelineRunner` in a background thread
5. Returns immediately — frontend connects to SSE for live updates

`PipelineRunner` calls existing execution scripts via `subprocess.run()`:

**Researcher phase:**
1. `scrape_website_content.py` — Playwright website scrape (fallback: company_description)
2. `scrape_google_reviews.py` — Google Maps reviews via Playwright
3. `analyze_lead_for_roi.py` — AI pain points + ROI (fallback: empty analysis)
4. `combine_research.py` — Merge all → research.json
5. `screenshot_website.py` — Old site screenshot

**Designer phase:**
6. `generate_spec_site.py` — OpenRouter API → index.html (NEW script)

**Judge phase:**
7. `screenshot_website.py` — New site screenshot
8. Programmatic quality check (responsive meta, phone links, reviews section, etc.) → score/100

**Ops phase:**
9. `deploy_spec_site.py` — Netlify deploy → live URL
10. `generate_outreach_email.py` — Personalized HTML email
11. `create_gmail_draft.py` — Gmail draft with inline CID images
12. `generate_followup_email.py` — Follow-up emails (day 3, 7, 14)
13. Creates email_sequence row in Supabase

Each step updates Supabase + emits SSE event → dashboard updates in real time.

## Email Sequence Flow

| Touch | Day | Type |
|---|---|---|
| 1 | 0 | Main pitch — spec site + before/after screenshots |
| 2 | +3 | Short bump — spec site link reminder |
| 3 | +7 | Pain point angle — research-backed revenue loss |
| 4 | +14 | Break-up — last chance, archive warning |

**Semi-auto sending:** Scheduler flags due sequences → Dashboard shows notification → User clicks Preview → Send. On send: draft sent via Gmail API, sequence advances, next send date calculated.

**Reply detection:** Every 5 minutes, checks Gmail threads for replies. If found: creates `replies` row, sets sentiment, stops the sequence, emits SSE notification.

## CSS Design System

Dark theme with these key variables:
```
--bg: #0a0e1a          --card: #111827         --card-border: #1e293b
--text: #e2e8f0         --text-dim: #64748b     --accent: #d4922a
--blue: #3b82f6         --green: #22c55e        --red: #ef4444
--purple: #a78bfa       --orange: #f59e0b       --pink: #f472b6
```

Badge classes: `.badge-hot`, `.badge-warm`, `.badge-cold`, `.badge-pending`, `.badge-completed`, `.badge-running`, `.badge-failed`, `.badge-sent`, `.badge-draft`, `.badge-replied`, `.badge-opened`, `.badge-bounced`, `.badge-active`, `.badge-paused`, `.badge-stopped_reply`

Agent card animations: `.agent-card.working::before` pulses blue, `.done` green, `.error` red.

## Key Existing Execution Scripts (not modified)

All in `../execution/` relative to pipeline-app:

| Script | What It Does |
|---|---|
| `scrape_website_content.py` | Playwright website scraper — `--url`, `--max_pages`, `--output` |
| `scrape_google_reviews.py` | Playwright Google Maps reviews — `--business_name`, `--location`, `--output` |
| `analyze_lead_for_roi.py` | OpenRouter AI analysis — `--website_data`, `--reviews_data`, `--company_name`, `--output` |
| `combine_research.py` | Merge all data sources — `--lead_json`, `--website`, `--reviews`, `--analysis`, `--output` |
| `screenshot_website.py` | Playwright screenshots — `--url`, `--output`, `--compress` |
| `deploy_spec_site.py` | Netlify API deploy — `--html`, `--slug`, `--output` |
| `generate_outreach_email.py` | OpenRouter email gen — `--company_data`, `--old_screenshot`, `--new_screenshot`, `--output_dir` |
| `create_gmail_draft.py` | Gmail OAuth draft — `--to`, `--subject`, `--html_file`, `--attach path:cid` |
| `generate_followup_email.py` | Follow-up emails — `--research`, `--all`, `--spec_url`, `--output_dir` |
| `track_lead_status.py` | Dedup + status — `--slug`, `--status`, `--check` |

## Lead Data Location

Ranked lead JSON files in `../.tmp/`:
- `hvac_ranked_20260215_214015.json` — main ranked leads file
- `hvac_ranked_pipeline.json`, `hvac_ranked_pipeline_next10.json` — additional batches
- `processed_leads.json` — tracks which leads are done
- Per-lead working dirs: `../.tmp/{slug}/` (research.json, index.html, screenshots, emails)

## Environment Variables Needed

In `../.env` (workspace root):
```
# ALREADY SET:
OPENROUTER_API_KEY=sk-or-v1-...
NETLIFY_AUTH_TOKEN=nfp_...
NETLIFY_SITE_ID=d5252f64-...
ANTHROPIC_API_KEY=...

# NEED TO ADD:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

Gmail OAuth files at workspace root: `gmail_token.json`, `gmail_credentials.json`

## Port

App runs on **port 5050** (not 5000 — macOS AirPlay uses 5000). Configurable via `PORT` env var.

## Known Issues / Quirks

1. `.env` line 35 (`password for email=...`) causes a harmless python-dotenv parse warning
2. Python 3.9 on this machine — some `importlib.metadata` deprecation warnings (non-blocking)
3. Templates have inline JS in `{% block scripts %}` that's self-contained — the separate `.js` files in `static/js/` provide the same functions but are loaded by `base.html` as backup
4. Pipeline runner uses `sys.executable` for subprocess — works with whatever Python started the app
5. Supabase client is lazy-initialized — app starts fine without credentials, just returns empty data/errors
