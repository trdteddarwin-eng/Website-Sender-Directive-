# Upwork Daily Pipeline — Automated Job Application System

Fully automated pipeline: scrape Upwork for AI/automation jobs via Bright Data, score relevance with Sonnet, generate proposals with Opus, output to Google Sheet.

## Quick Start

```bash
# Full run (~$1.50-2.50)
python execution/upwork_daily_pipeline.py

# Dry run — scrape + filter only, no AI costs
python execution/upwork_daily_pipeline.py --dry-run

# Small test run
python execution/upwork_daily_pipeline.py --limit 10 --workers 1

# Clear dedup store (re-process previously seen jobs)
python execution/upwork_daily_pipeline.py --reset-seen
```

## Pipeline Flow (3 Phases)

### Phase 1: Scrape + Deterministic Filters (free)
1. Load config from `execution/upwork_pipeline_config.json`
2. Load dedup store from `.tmp/upwork_seen_jobs.json`
3. For each keyword, scrape Upwork search via Bright Data MCP (`scrape_as_markdown`)
4. Union all results, deduplicate by job ID (across keywords + seen store)
5. Apply deterministic filters:
   - Verified payment only
   - Min client spend ($100+)
   - Experience level (intermediate/expert)
   - Budget threshold ($500+ fixed / $25+ hourly)
   - Skip jobs with 20+ proposals (too competitive)
6. If zero jobs pass → exit

### Phase 2: AI Relevance Scoring — Sonnet 4.5 (~$0.10)
7. Score each job 1-10 for relevance to skills profile
8. Criteria: AI/automation, n8n, voice AI, workflow, API integration match
9. Flag red flags: vague descriptions, scope mismatch, unrealistic budgets
10. Filter to jobs scoring 7+ (configurable)

### Phase 3: Proposal Generation — Opus 4.5 (~$1-2)
11. Save qualified jobs to `.tmp/upwork_jobs_YYYY-MM-DD.json`
12. For each qualified job (parallel, 3 workers):
    - Discover contact name
    - Generate proposal + Google Doc
    - Generate cover letter
13. Create Google Sheet `Upwork Proposals - YYYY-MM-DD`
14. Write all results to sheet (includes relevance score)
15. Update dedup store

## Config

`execution/upwork_pipeline_config.json`:

| Field | Default | Description |
|-------|---------|-------------|
| `keywords` | 9 AI/automation terms | Search terms to scrape |
| `days` | 1 | Only jobs from last N days |
| `workers` | 3 | Parallel Opus workers |
| `filters.verified_payment` | false | Require verified payment (disabled — not available via MCP) |
| `filters.min_client_spent` | 0 | Min $ client has spent (disabled — not available via MCP) |
| `filters.min_fixed_budget` | 500 | Min fixed-price budget |
| `filters.min_hourly_rate` | 25 | Min hourly rate |
| `filters.max_proposals` | 20 | Skip jobs with 20+ proposals |
| `filters.experience_levels` | intermediate, expert | Required levels |
| `qualification.model` | claude-sonnet-4-5-20250929 | Scoring model |
| `qualification.min_score` | 7 | Min relevance score (1-10) |
| `qualification.skills_profile` | AI/automation skills | Profile for scoring |

## Cost Per Run

| Phase | Component | Cost |
|-------|-----------|------|
| 1 | Bright Data (9 keyword searches) | ~$0.05-0.10 |
| 1 | Deterministic filters | $0 |
| 2 | Sonnet 4.5 (~30 jobs) | ~$0.10 |
| 3 | Opus 4.5 (~10-15 jobs x 3 calls) | ~$1-2 |
| 3 | Google Docs/Sheets API | $0 |
| | **Total per run** | **~$1.50-2.50** |

## Execution Tools

| Script | Purpose |
|--------|---------|
| `execution/upwork_daily_pipeline.py` | Main orchestrator |
| `execution/upwork_brightdata_scraper.py` | Bright Data MCP scraper (`scrape_as_markdown`) |
| `execution/upwork_proposal_generator.py` | Proposal generation (imported, not run standalone) |
| `execution/upwork_pipeline_config.json` | Pipeline configuration |

### Standalone Scraper
```bash
# Single keyword
python execution/upwork_brightdata_scraper.py --keyword "ai agent" -o .tmp/test_jobs.json

# Multiple keywords
python execution/upwork_brightdata_scraper.py --keywords "ai agent,n8n,voice ai" --days 1
```

## Output

Google Sheet with columns:
| Column | Description |
|--------|-------------|
| Title | Job title |
| URL | Job listing URL |
| Budget | Fixed price or hourly range |
| Experience | Required level |
| Skills | Top 5 required skills |
| Category | Job category |
| Client Country | Client location |
| Client Spent | Total $ spent on platform |
| Client Hires | Total past hires |
| Connects | Cost to apply |
| **Relevance Score** | AI-scored relevance (1-10) |
| **Relevance Notes** | Why this score |
| Contact Name | Discovered first name |
| Contact Confidence | high/medium/low |
| Apply Link | One-click apply URL |
| Cover Letter | Personalized pitch |
| Proposal Doc | Google Doc with full proposal |

## Deduplication

- Seen job IDs stored in `.tmp/upwork_seen_jobs.json`
- Auto-prunes entries older than 30 days
- `--reset-seen` flag clears the store
- Jobs are marked as seen after each run (even if they don't pass filters)

## Edge Cases

- **No jobs found**: Check Bright Data MCP token, try broader keywords
- **MCP scrape timeout**: Some keywords take 60-120s. Default timeout is 180s. If persistent, check MCP token validity.
- **Keyword scrape fails**: Pipeline continues with remaining keywords (fail-open per keyword)
- **Sonnet scoring error**: Job is included anyway (fail open)
- **Opus rate limit**: Reduce `--workers` to 1-2
- **Google Doc creation fails**: Retries 4x with exponential backoff
- **Dedup store corrupted**: Use `--reset-seen` to clear

## Learnings

- Bright Data MCP uses SSE transport at `https://mcp.brightdata.com/sse?token=...`
- MCP `scrape_as_markdown` returns markdown (NOT raw HTML). Parse markdown to extract job listings.
- SSE responses contain large JSON with newlines inside text — must use `iter_content()` with manual `\n\n` event parsing (NOT `iter_lines()`)
- MCP scrape takes 60-120 seconds per keyword. Some keywords may timeout — 180s timeout is recommended.
- Markdown scraper CANNOT extract client metadata (payment verified, spend, hires) — those filters are disabled
- `verified_payment` and `min_client_spent` filters disabled in config (data not available via markdown)
- Dedup store prevents re-processing jobs across runs
- 3-phase approach saves ~50% on Opus costs vs scoring everything
- Proposal generator uses `threading.Semaphore(1)` for Google Doc creation
- Opus model ID: `claude-opus-4-5-20251101`
- Sonnet model ID: `claude-sonnet-4-5-20250929`
