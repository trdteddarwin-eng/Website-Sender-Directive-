# Upwork Auto-Apply System

## Goal

Automatically find, qualify, and apply to Upwork jobs with custom deliverables (spec sites for website jobs, animated flowchart videos for automation jobs). Runs every 2 hours on Modal during business hours (Mon-Fri, 9am-6pm EST). Zero manual intervention once deployed -- scrape, score, build, apply, track.

## System Overview

### Architecture

```
Apify Scraper → Sonnet Classifier → Deliverable Builder → Opus Cover Letter → Playwright Applier → Supabase Tracker
```

### Components

| File | Purpose | Cost |
|------|---------|------|
| `upwork-auto-apply/config.json` | Pipeline config (keywords, filters, scoring, auto-apply settings) | -- |
| `upwork-auto-apply/pipeline.py` | Main 6-phase orchestrator | -- |
| `upwork-auto-apply/classifier.py` | AI scoring + job classification (website/automation/other) | ~$0.003/job |
| `upwork-auto-apply/site_generator.py` | Spec site builder (3 parallel Kimi K2.5 calls) | ~$0.10/site |
| `upwork-auto-apply/vercel_deployer.py` | Deploy HTML to Vercel, return live URL | Free |
| `upwork-auto-apply/flowchart_generator.py` | Automation flowchart data generator (Opus 4.6 via OpenRouter) | ~$0.05/video |
| `upwork-auto-apply/remotion-flowchart/` | Remotion project for animated flowchart rendering | Free (local) |
| `upwork-auto-apply/applier.py` | Playwright auto-apply on Upwork (stealth mode + selectors) | Connects |
| `upwork-auto-apply/session_manager.py` | Cookie persistence via Supabase (load/save/health check) | Free |
| `upwork-auto-apply/login_helper.py` | One-time headed browser cookie capture | Free |
| `upwork-auto-apply/tracker.py` | Supabase CRUD for applications + daily stats | Free |
| `upwork-auto-apply/selector_config.json` | CSS selectors for Upwork UI (externalized for easy updates) | -- |
| `upwork-auto-apply/modal_deploy.py` | Modal deployment + cron scheduling | Free tier |

---

## Pipeline Phases

### Phase 1: Scrape + Filter (free)

1. Apify `clockworks/tiktok-scraper` (or Upwork-specific actor) scrapes **9 keywords x 50 jobs each** = up to 450 raw jobs
2. Dedup against Supabase via `tracker.check_already_applied(job_id)`
3. Apply deterministic filters from `config.json`:
   - `max_connects_cost`: 4 (keeps cost per apply low)
   - `min_fixed_budget`: $500+ fixed-price / `min_hourly_rate`: $25+ hourly
   - `max_proposals`: 15 (skip saturated jobs)
   - `experience_levels`: intermediate, expert only

**Expected output:** ~30-80 jobs after dedup + filtering.

### Phase 2: AI Score + Classify (~$0.003/job)

1. Each job goes through `classifier.py` which makes a single Sonnet 4.5 (`claude-sonnet-4-5-20250929`) API call
2. Returns:
   - **Relevance score** (1-10): how well the job matches the skills profile
   - **Job type classification**: `website`, `automation`, or `other`
3. Filter: keep only jobs scoring >= `scoring.min_score` (default: 8)

**Skills profile** (from `classifier.py`):
> AI/automation, n8n workflows, voice AI agents, API integrations, Claude/GPT apps, website development, landing pages

**Expected output:** ~5-15 qualified jobs.

### Phase 3: Build Deliverable (~$0.10-0.15/job)

Deliverable depends on job classification:

| Job Type | Script | Deliverable | Deploy |
|----------|--------|-------------|--------|
| `website` | `site_generator.py` | Custom spec site (single-page HTML) | Vercel via `vercel_deployer.py` |
| `automation` | `flowchart_generator.py` + Remotion | Animated flowchart video | Upload + URL |
| `other` | -- | No deliverable | -- |

#### Website Jobs: Spec Site Builder

`site_generator.py` generates a complete single-page HTML site via **3 parallel Kimi K2.5 calls** (top/middle/bottom sections, ~5K tokens each). CSS framework is Python-generated (deterministic). This avoids the timeout issues from monolithic 16K-token calls.

```bash
python3 upwork-auto-apply/site_generator.py \
    --job-title "Modern Plumbing Website" \
    --job-description "We need a clean, modern website for our plumbing company..." \
    --palette 2 \
    --hero-style 1 \
    --output .tmp/acme-plumbing/index.html
```

Then deploy to Vercel:
```bash
python3 upwork-auto-apply/vercel_deployer.py \
    --html-file .tmp/acme-plumbing/index.html \
    --project-name acme-plumbing-demo
```

Returns a live URL like `https://acme-plumbing-demo.vercel.app`.

#### Automation Jobs: Flowchart Video

`flowchart_generator.py` uses Opus 4.6 (`anthropic/claude-opus-4-6`) via OpenRouter to analyze the job and generate a flowchart definition (nodes, edges, colors, icons). This feeds into the `remotion-flowchart/` Remotion project for rendering an animated video.

```bash
python3 upwork-auto-apply/flowchart_generator.py \
    --job-title "Automate Lead Scoring" \
    --job-description "We need an n8n workflow that scores incoming leads..."
```

Returns: `{ title, nodes: [{id, label, icon, color}], edges: [...] }`

### Phase 4: Generate Cover Letter (~$0.12/job)

Opus 4.5 (`claude-opus-4-5-20251101`) generates a personalized cover letter. The tone and structure depend on job type:

| Job Type | Cover Letter Template |
|----------|----------------------|
| `website` | "Hi. I work with [paraphrase of their needs] daily & just built a mock for you: [vercel_url]" |
| `automation` | "Hi. I work with [paraphrase of their needs] daily & mapped out how I'd build it: [video_url]" |
| `other` | Standard cover letter without deliverable link |

Key rules:
- Open with "Hi." -- not "Dear Client" or "Hello!"
- Paraphrase their job description -- don't repeat it verbatim
- Lead with the deliverable URL (the hook)
- Keep it under 200 words
- No fluff, no "I'm excited to apply"
- Close with a concrete next step

### Phase 5: Auto-Apply (connects cost)

`applier.py` uses Playwright with stealth settings to submit each application on Upwork:

1. **Load session** from Supabase via `session_manager.load_session()`
2. **Health check** via `session_manager.check_session_health()` -- verify not redirected to login
3. **Navigate** to job URL
4. **Fill application**:
   - Paste cover letter into `cover_letter_textarea`
   - Set rate/bid via `hourly_rate_input` or `fixed_price_input`
   - Disable boost via `boost_toggle` + `boost_off_option` (config: `skip_boost: true`)
5. **Submit** via `submit_button`
6. **Verify** success via `success_indicator`
7. **Screenshot** for audit trail
8. **Record** in Supabase via `tracker.record_application()`

Selectors are externalized in `selector_config.json` -- update this file when Upwork changes their UI.

**Safety limits enforced per run:**
- Random delay between applies: 45-120 seconds (configurable in `auto_apply.delay_between_applies_sec`)
- Daily application limit: 10 (configurable in `auto_apply.daily_application_limit`)
- Daily connects budget: 40 (configurable in `auto_apply.daily_connects_budget`)
- Budget check via `tracker.check_daily_budget()` before each application

```bash
# Test a single apply with visible browser
python3 upwork-auto-apply/applier.py \
    --job-url "https://www.upwork.com/..." \
    --cover-letter "Hi. I just built a mock for you..." \
    --rate 75 \
    --headed \
    --screenshot-dir ./screenshots
```

### Phase 6: Report

1. Update daily stats in Supabase via `tracker.update_daily_stats()`:
   - `jobs_scraped`, `jobs_filtered`, `jobs_scored`, `jobs_applied`
   - `sites_built`, `videos_made`, `connects_spent`, `errors`
2. Email summary if configured (`notifications.email_on_apply: true`)
3. Email alert on errors or expired sessions

---

## Running the Pipeline

### Dry run (free, no API costs)

Scrape + filter only. Shows what jobs would be scored and applied to without spending anything.

```bash
python upwork-auto-apply/pipeline.py --dry-run
```

### Dry run with deliverables (builds sites/videos but doesn't apply)

Tests the full pipeline except the actual Upwork submission. Good for verifying site quality and cover letters.

```bash
python upwork-auto-apply/pipeline.py --dry-run --with-deliverables
```

### Single apply test (visible browser)

Processes one job end-to-end with a headed browser so you can watch the apply happen.

```bash
python upwork-auto-apply/pipeline.py --limit 1 --headed
```

### Full run

```bash
python upwork-auto-apply/pipeline.py
```

### Deploy to Modal (scheduled runs)

```bash
modal deploy upwork-auto-apply/modal_deploy.py
```

Schedule: `0 */2 14-23 * * 1-5` = every 2 hours, Mon-Fri, 9am-6pm EST (14:00-23:00 UTC).

---

## Setup Steps

### 1. Supabase Tables

Run these SQL statements in the Supabase SQL editor (one-time setup):

```sql
-- Application tracking
CREATE TABLE upwork_applications (
    id SERIAL PRIMARY KEY,
    job_id TEXT UNIQUE NOT NULL,
    job_title TEXT,
    job_url TEXT,
    job_budget TEXT,
    job_type TEXT,                        -- 'website' | 'automation' | 'other'
    relevance_score INTEGER,
    cover_letter TEXT,
    bid_amount NUMERIC,
    deliverable_url TEXT,                 -- Vercel site URL or video URL
    status TEXT DEFAULT 'pending',        -- pending -> applied -> failed
    connects_spent INTEGER DEFAULT 0,
    applied_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily aggregate stats
CREATE TABLE upwork_daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    jobs_scraped INTEGER DEFAULT 0,
    jobs_filtered INTEGER DEFAULT 0,
    jobs_scored INTEGER DEFAULT 0,
    jobs_applied INTEGER DEFAULT 0,
    sites_built INTEGER DEFAULT 0,
    videos_made INTEGER DEFAULT 0,
    connects_spent INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Browser session (cookie) persistence
CREATE TABLE upwork_sessions (
    id SERIAL PRIMARY KEY,
    session_name TEXT UNIQUE DEFAULT 'default',
    cookies JSONB NOT NULL,
    user_agent TEXT,
    viewport JSONB DEFAULT '{"width": 1920, "height": 1080}',
    last_verified TIMESTAMPTZ,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Environment Variables

Add to `.env` (in workspace root):

```bash
# Already set (existing):
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
APIFY_API_TOKEN=apify_api_...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# New (required for this pipeline):
VERCEL_TOKEN=...               # From vercel.com/account/tokens
```

### 3. Dependencies

```bash
pip install playwright anthropic supabase-py python-dotenv requests
playwright install chromium
```

### 4. Login Cookies

Run once to capture Upwork session cookies. A headed browser opens -- log in manually (including 2FA), then press Enter.

```bash
python upwork-auto-apply/login_helper.py
```

Cookies are saved to Supabase (`upwork_sessions` table). The pipeline loads them automatically before each apply session.

**Re-run every 2-4 weeks** when cookies expire. The pipeline will auto-pause and send an email alert if the session health check fails (redirected to login page).

### 5. Remotion Setup (for flowchart videos)

```bash
cd upwork-auto-apply/remotion-flowchart && npm install
```

### 6. Deploy to Modal

```bash
modal deploy upwork-auto-apply/modal_deploy.py
```

Verify the scheduled function appears in your Modal dashboard.

---

## Configuration Reference

All settings live in `upwork-auto-apply/config.json`:

### Keywords

```json
"keywords": ["automation", "ai agent", "n8n", "gpt", "workflow", "api integration", "voice ai", "ai consultant", "app developer"]
```

9 keywords, 50 jobs each = up to 450 raw jobs per scrape.

### Filters (Deterministic, Free)

| Setting | Default | Description |
|---------|---------|-------------|
| `filters.min_fixed_budget` | 500 | Min fixed-price budget in USD |
| `filters.min_hourly_rate` | 25 | Min hourly rate in USD |
| `filters.max_proposals` | 15 | Skip jobs with more proposals than this |
| `filters.max_connects_cost` | 4 | Max connects per job (keeps cost per apply low) |
| `filters.experience_levels` | `["intermediate", "expert"]` | Skip entry-level jobs |

### Scoring (AI, ~$0.003/job)

| Setting | Default | Description |
|---------|---------|-------------|
| `scoring.model` | `claude-sonnet-4-5-20250929` | Model for relevance scoring |
| `scoring.min_score` | 8 | Minimum relevance score (1-10) to proceed |

### Proposal (AI, ~$0.12/job)

| Setting | Default | Description |
|---------|---------|-------------|
| `proposal.model` | `claude-opus-4-5-20251101` | Model for cover letter generation |

### Deliverable (AI, ~$0.10/job)

| Setting | Default | Description |
|---------|---------|-------------|
| `deliverable.site_model` | `moonshotai/kimi-k2.5` | Model for spec site generation (via OpenRouter) |
| `deliverable.flowchart_model` | `anthropic/claude-opus-4-6` | Model for flowchart data generation (via OpenRouter) |
| `deliverable.vercel_team` | `null` | Vercel team ID (null = personal account) |

### Auto-Apply (Connects Cost)

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_apply.enabled` | `true` | Master switch for auto-apply |
| `auto_apply.mode` | `"full_auto"` | `full_auto` or `review_first` |
| `auto_apply.daily_application_limit` | 10 | Max applications per day |
| `auto_apply.daily_connects_budget` | 40 | Max connects to spend per day |
| `auto_apply.default_hourly_rate` | 75 | Default hourly rate bid in USD |
| `auto_apply.skip_boost` | `true` | Disable boost on applications |
| `auto_apply.delay_between_applies_sec` | `[45, 120]` | Random delay range (seconds) between applies |

### Schedule

| Setting | Default | Description |
|---------|---------|-------------|
| `schedule.cron` | `0 */2 14-23 * * 1-5` | Every 2h, Mon-Fri, 9am-6pm EST (UTC offset) |

### Notifications

| Setting | Default | Description |
|---------|---------|-------------|
| `notifications.email_on_apply` | `true` | Email after each successful apply |
| `notifications.email_on_error` | `true` | Email on pipeline errors |
| `notifications.email_on_session_expired` | `true` | Email when Upwork session expires |

---

## Cost Estimate (~$90-150/month)

Assuming 3-5 applications per day, 22 business days per month:

| Category | Calculation | Monthly Cost |
|----------|-------------|-------------|
| Upwork connects | 3-5 apps/day x 3 avg connects x $0.15/connect x 22 days | $30-50 |
| Opus 4.5 (cover letters) | ~4 apps/day x $0.12 x 22 days | $10-15 |
| Kimi K2.5 (spec sites) | ~2 sites/day x $0.10 x 22 days | $4-10 |
| Opus 4.6 (flowcharts) | ~1 video/day x $0.05 x 22 days | $1-3 |
| Sonnet 4.5 (scoring) | ~50 jobs/day x $0.003 x 22 days | $3-5 |
| Vercel hosting | Free tier (hobby) | $0 |
| Supabase | Free tier | $0 |
| Modal | Free tier | $0 |
| Apify | **Hard cap: $0.50/run** (3 keywords max per run) | $0-5 |
| **Total** | | **~$50-90** |

---

## Tracker CLI

`tracker.py` has a CLI for inspecting pipeline state:

```bash
# Check daily budget (can we still apply today?)
python upwork-auto-apply/tracker.py check-budget --limit 10 --connects 40

# View today's stats
python upwork-auto-apply/tracker.py stats

# View stats for a specific date
python upwork-auto-apply/tracker.py stats --date 2026-02-21

# List recent applications (last 7 days)
python upwork-auto-apply/tracker.py recent --days 7

# Check if already applied to a specific job
python upwork-auto-apply/tracker.py check-applied <job_id>

# Record a test application (for debugging)
python upwork-auto-apply/tracker.py record --job-id test123 --title "Test Job" --type website --score 9
```

---

## Troubleshooting

### Session Expired

**Symptom:** Pipeline logs "Session invalid -- redirected to login page". Email alert sent.

**Fix:**
```bash
python upwork-auto-apply/login_helper.py
```
Log in via the headed browser, press Enter. Cookies are saved to Supabase. Next pipeline run will pick them up automatically.

**Prevention:** Re-run `login_helper.py` proactively every 2-3 weeks before cookies expire.

### Selectors Broken (Upwork UI Changed)

**Symptom:** Playwright can't find the cover letter textarea, submit button, or other elements. Apply fails with timeout.

**Fix:**
1. Open the Upwork apply page in a regular browser
2. Inspect the elements and find the new selectors
3. Update `upwork-auto-apply/selector_config.json` with the new CSS selectors
4. Test with a single headed apply:

```bash
python upwork-auto-apply/applier.py --job-url <url> --cover-letter "test" --rate 75 --headed
```

### Budget Exhausted

**Symptom:** `tracker.check_daily_budget()` returns `can_apply: false`. Pipeline skips apply phase.

**Fix:** This is by design -- daily limits protect against runaway spending. If you want to increase limits, update `config.json`:
- `auto_apply.daily_application_limit` (default: 10)
- `auto_apply.daily_connects_budget` (default: 40)

Budget resets at midnight (UTC).

### Site Generation Timeout

**Symptom:** Kimi K2.5 call times out for spec site generation.

**Fix:** `site_generator.py` already splits into 3 parallel API calls (~5K tokens each) with 180s timeout and 1 retry per call. If still timing out:
- Check OpenRouter status
- Reduce complexity in the prompt
- Fall back to a simpler template

**Rule from CLAUDE.md:** Never ask Kimi K2.5 for >6K output tokens in a single call. Split large generations into parallel sections.

### Vercel Deploy Fails

**Symptom:** `vercel_deployer.py` returns None instead of a URL.

**Fix:**
1. Verify `VERCEL_TOKEN` in `.env` is valid
2. Check Vercel API status
3. Try deploying manually: `vercel deploy --prod` from the site directory

### Flowchart Video Render Fails

**Symptom:** Remotion render fails or produces empty video.

**Fix:**
1. Verify Remotion is set up: `cd upwork-auto-apply/remotion-flowchart && npm install`
2. Check that `flowchart_generator.py` output has valid node/edge data
3. Test Remotion render standalone: `npx remotion render FlowchartVideo out.mp4`

### No Jobs Found After Filtering

**Symptom:** Phase 1 returns 0 jobs after filters.

**Possible causes:**
- Keywords too narrow -- check `config.json` keywords array
- Filters too strict -- temporarily relax `max_connects_cost` or `min_fixed_budget`
- Apify scraper actor down -- check Apify dashboard
- All jobs already in Supabase (dedup working correctly) -- this is normal for frequent runs

---

## Selector Config Reference

`selector_config.json` maps logical actions to CSS selectors. All selectors use fallback chains (comma-separated) for resilience:

```json
{
  "apply_page": {
    "cover_letter_textarea": "textarea[aria-labelledby*='cover_letter'], textarea[data-test='cover-letter-area'], #cover_letter",
    "hourly_rate_input": "input[aria-label*='hourly rate'], input[data-test='rate-input'], input[name='rate']",
    "fixed_price_input": "input[aria-label*='bid'], input[data-test='bid-input']",
    "boost_toggle": "button[data-test='boost-toggle'], input[type='checkbox'][aria-label*='boost'], .boost-toggle",
    "boost_off_option": "[data-test='boost-none'], [aria-label*='No boost']",
    "submit_button": "button[data-test='submit-proposal'], button[type='submit']:has-text('Submit'), button:has-text('Submit a Proposal')",
    "success_indicator": "[data-test='proposal-submitted'], .success-message, :has-text('Your proposal was submitted')",
    "connects_cost_display": "[data-test='connects-cost'], .connects-required, :has-text('Connects')",
    "error_message": "[data-test='error-message'], .error-banner, [role='alert']"
  },
  "login_check": {
    "logged_in_indicator": "[data-test='user-menu'], .nav-user-menu, .user-avatar",
    "login_redirect": "/ab/account-security/login"
  }
}
```

---

## Data Flow Summary

```
config.json (keywords, filters, models)
    │
    ▼
[Phase 1] Apify Scraper
    │  9 keywords x 50 jobs = ~450 raw
    ▼
[Dedup] tracker.check_already_applied()
    │  Remove jobs already in Supabase
    ▼
[Filter] Deterministic (budget, connects, experience)
    │  ~30-80 jobs remain
    ▼
[Phase 2] classifier.py (Sonnet 4.5)
    │  Score 1-10, classify: website/automation/other
    │  Keep score >= 8
    │  ~5-15 jobs remain
    ▼
[Phase 3] Deliverable Builder
    │  website → site_generator.py → vercel_deployer.py → live URL
    │  automation → flowchart_generator.py → Remotion → video URL
    │  other → skip
    ▼
[Phase 4] Cover Letter (Opus 4.5)
    │  Personalized with deliverable URL
    ▼
[Phase 5] applier.py (Playwright)
    │  Load cookies → navigate → fill → submit → screenshot
    │  45-120s delay between applies
    │  Budget check before each apply
    ▼
[Phase 6] Report
    │  tracker.update_daily_stats()
    │  Email summary
    ▼
Supabase (upwork_applications, upwork_daily_stats)
```

---

## Lessons Learned

<!-- Append entries here as issues are discovered. Follow the CLAUDE.md error log format. -->

### [2026-02-23] Apify budget blown — 9 keyword runs cost $1.35
- **What happened:** Pipeline ran 9 sequential Apify scrape runs (one per keyword), each costing $0.15. Total: $1.35 in one pipeline execution.
- **Why:** No per-run budget cap. Each keyword triggers a separate Apify actor run at $0.15 each.
- **Fix:** Added $0.50 hard cap per pipeline run. Reduce keywords per run to max 3. Reuse cached Apify dataset results (free to read back) instead of re-scraping.
- **Rule:** **Apify budget: $0.50 max per pipeline run.** Before scraping, calculate cost: keywords × $0.15. If over $0.50, reduce keywords or batch across runs. Always check Apify datasets from prior runs before re-scraping. Reading cached data is free.

### [2026-02-23] max_connects_cost: 4 filters out ALL jobs
- **What happened:** All 9 keyword-matched jobs were filtered out in Phase 1. Zero jobs reached scoring.
- **Why:** Upwork now charges 8-25 connects per application. `max_connects_cost: 4` is impossibly low.
- **Fix:** Changed to `max_connects_cost: 16`. Also fixed `fixedBudget: 0` bug — Apify returns `0` (not null) for hourly jobs, causing them to fail the min_fixed_budget check. Changed `if fixed is not None` to `if fixed` (truthy).
- **Rule:** Upwork connects cost is typically 8-16 for AI/automation jobs. Never set max_connects below 8. Also: `fixedBudget: 0` from Apify means "hourly job", not "$0 fixed" — always check truthiness, not None.

### [Template] Short description
- **What happened:** What went wrong
- **Why:** Root cause
- **Fix:** What was done to fix it
- **Rule:** The permanent rule to follow so this never happens again
