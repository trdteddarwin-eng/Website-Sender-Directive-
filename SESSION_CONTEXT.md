# TedCA Pipeline Dashboard — Session Context

Use this to onboard a new Claude session. Copy the prompt at the bottom.

---

## What This System Does

TedCA is an automated HVAC lead outreach pipeline. It takes leads from Supabase, researches each company, generates a custom "spec website," deploys it to Netlify, drafts personalized outreach emails with before/after screenshots, and manages a 4-touch email sequence — all from a Flask dashboard.

**The pipeline flow for each lead:**
1. **Researcher** — Scrape website + Google reviews, run AI analysis (pain points, ROI)
2. **Designer** — Generate full custom HTML spec site via OpenRouter API
3. **Judge** — Screenshot new site, run quality checks + K2.5 visual review (score 0-100)
4. **Ops** — Deploy to Netlify, generate outreach email + 3 follow-ups, create drafts, create sequence

---

## Architecture

**3-Layer System** (see `CLAUDE.md` for full details):
- **Directives** (`directives/`) — SOPs in Markdown
- **Orchestration** — Claude reads directives, calls tools, handles errors
- **Execution** (`execution/`) — 80+ deterministic Python scripts

---

## Key Directories

```
/Users/yoljean/Downloads/Ted Workspace/
├── CLAUDE.md                 # Agent instructions + error log (READ FIRST)
├── SESSION_CONTEXT.md        # This file
├── .env                      # API keys (OPENROUTER, NETLIFY, ANTHROPIC, KIE, SUPABASE)
├── directives/               # SOPs
├── execution/                # Python scripts (80+)
├── pipeline-app/             # Flask web dashboard
│   ├── app.py                # Entry point — python3 pipeline-app/app.py (port 5050)
│   ├── config.py             # Loads .env, defines paths
│   ├── schema.sql            # Full Supabase schema with ALTER TABLE migrations
│   ├── services/
│   │   ├── supabase_client.py  # Data layer — ALL database operations
│   │   ├── pipeline_runner.py  # 4-phase pipeline orchestrator (background thread)
│   │   ├── smtp_sender.py      # SMTP email sending via @tedca.online accounts
│   │   ├── daily_queue_service.py  # Daily send queue generation + execution
│   │   ├── auto_reply_service.py   # AI-drafted replies to incoming emails
│   │   ├── inbox_service.py    # IMAP inbox polling for @tedca.online accounts
│   │   ├── sequence_scheduler.py   # APScheduler: reply checks, queue generation
│   │   └── sse_manager.py     # Server-Sent Events for live pipeline updates
│   ├── blueprints/
│   │   ├── api.py              # ALL JSON API endpoints
│   │   ├── dashboard.py        # GET / — KPIs
│   │   ├── leads.py            # GET /leads, /leads/<slug>
│   │   ├── pipeline.py         # GET /pipeline — live agent monitor + SSE stream
│   │   ├── drafts.py           # GET /drafts — email drafts + compose
│   │   ├── sequences.py        # GET /sequences
│   │   ├── analytics.py        # GET /analytics
│   │   └── settings.py         # GET /settings
│   ├── templates/              # Jinja2 HTML
│   └── static/                 # CSS + JS
└── .tmp/{slug}/                # Per-lead working directory (research, HTML, screenshots)
```

---

## Data Layer

**Database:** Supabase (Postgres) — accessed via `supabase-py` REST client.

**Tables (9):**
| Table | Purpose |
|-------|---------|
| `leads` | Lead profiles, tier, score, pipeline_status |
| `pipeline_runs` | Per-run status, agent states (JSONB), logs, timestamps |
| `spec_sites` | Deploy URL, judge_score, HTML content |
| `emails` | Subject, body, recipient, touchpoint, status, sender_account |
| `email_sequences` | Per-lead sequence status, current touchpoint, next_send_date, sender_account |
| `replies` | Inbound replies, sentiment classification |
| `auto_replies` | AI-drafted reply management |
| `activity_log` | Event timeline for all pipeline + email activity |
| `daily_queue` | Daily send queue items |

**Env vars:** `SUPABASE_URL`, `SUPABASE_KEY` in `.env`

---

## Email System

- **Sending:** SMTP via @tedca.online accounts (not Gmail API)
- **Sender rotation:** Round-robin across accounts, max sends per day per account
- **Sequences:** 4-touch with configurable delays (3, 4, 7 days)
- **Inbox:** IMAP polling for replies on @tedca.online accounts
- **Auto-replies:** AI drafts responses to incoming emails

---

## What Was Built in Last Session (Feb 20, 2026)

### 1. Compose Email from Drafts Page
- Compose button + modal on `/drafts` (To, Subject, Sender, Body)
- `POST /api/emails/compose` creates standalone drafts
- Auto-links to existing leads by email

### 2. Run Specific Lead from Pipeline Page
- "Run Lead..." search modal with typeahead
- `GET /api/leads/search?q=...` endpoint

### 3. Pipeline Resume / Retry
- `POST /api/pipeline/resume` resumes failed runs from where they crashed
- Skips agents already marked "done", preserves `.tmp/` files
- "Retry from Failure" button on banner + "Retry" on failed rows in Recent Runs

### 4. Pipeline State Persistence
- `/api/pipeline/status` returns `last_run` when no active run (failed/completed)
- Page reload restores agent cards, completed tasks, log, retry button from Supabase

### 5. Schema Fix
- `email_sequences.sender_account` column was missing — caused pipelines to crash at OPS finish
- Fixed via `ALTER TABLE` in Supabase SQL Editor
- Added try/catch fallback in pipeline_runner.py
- Updated schema.sql with all missing columns

---

## How to Run

```bash
cd "/Users/yoljean/Downloads/Ted Workspace/pipeline-app"
python3 app.py
# → http://localhost:5050
```

---

## Known Issues / Gaps

1. **Email open/click/bounce tracking** — `open_count` column exists but never updates. No tracking pixel.
2. **Spec site analytics** — No way to know if leads visit deployed sites.
3. **`.env` line 35** — `password for email=...` causes python-dotenv parse warning. Harmless but noisy.
4. **Error details** — Pipeline failures log generically; stack traces only in `log-processes/errors.log`.

---

## GitHub Repo

`https://github.com/trdteddarwin-eng/Website-Sender-Directive-.git`
Branch: `main`, last commit: `9820e48`

---

## Prompt for New Claude Session

Copy and paste this:

```
I'm working on the TedCA Pipeline Dashboard — a Flask app at `pipeline-app/` that automates HVAC lead outreach: research, spec site generation, Netlify deploy, email drafting, and SMTP sending.

Read these files first:
1. `CLAUDE.md` — Agent instructions, 3-layer architecture, error log
2. `SESSION_CONTEXT.md` — Full system overview, what was built last session, current state

Key architecture:
- Data: Supabase (Postgres) via supabase-py. Schema in `pipeline-app/schema.sql`
- Pipeline: 4 agents (researcher → designer → judge → ops) in `services/pipeline_runner.py`
- API: All endpoints in `blueprints/api.py`
- Email: SMTP via @tedca.online accounts, NOT Gmail API
- Frontend: Jinja2 templates + vanilla JS, SSE for live updates

Last session (Feb 20) we added: compose emails from drafts page, run specific leads via search modal, resume/retry failed pipeline runs, pipeline state persistence across page reloads, and fixed a missing `sender_account` column on `email_sequences` that crashed every pipeline at the OPS step.

The app runs on localhost:5050. Git repo: github.com/trdteddarwin-eng/Website-Sender-Directive- (main branch).
```
