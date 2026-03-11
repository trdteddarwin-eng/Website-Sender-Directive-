# Agent Instructions

You operate within a 3-layer architecture: directives define intent, you orchestrate decisions, deterministic scripts execute work. This separation prevents compounding LLM errors.

## Architecture

**Layer 1: Directive** — SOPs in `directives/`. Define goals, inputs, tools, outputs, and edge cases.

**Layer 2: Orchestration** — You. Read directives, call execution scripts in order, handle errors, update directives with learnings. You don't scrape websites yourself — you run `execution/scrape_single_site.py`.

**Layer 3: Execution** — Deterministic Python scripts in `execution/`. API calls, data processing, file I/O, database ops. Reliable, testable, fast.

**Why:** 90% accuracy per step = 59% over 5 steps. Push complexity into deterministic code.

## Second Brain (`brain/`)

The user's second brain lives in `brain/`. Structure: `HOME.md`, `clients/`, `projects/`, `daily/`, `ideas/`, `templates/`.

**Rules:**
1. **Read `brain/HOME.md` at the start of every session** to know what the user is working on.
2. **Never edit any file in `brain/` silently.** This includes HOME.md, projects, clients, ideas, daily logs — everything. Always tell the user: which file, what you're changing, and why — before making the edit. Wait for acknowledgment.
3. **Update `brain/HOME.md`** when projects change status, new decisions are made, or priorities shift.
4. **Log new contacts** in `brain/clients/` using the template in `brain/templates/client.md`.
5. **Capture ideas** in `brain/ideas/index.md` instead of immediately building them.
6. This is a general-purpose knowledge base — not limited to any single project.

## Operating Principles

1. **Check `execution/` first.** Before writing a script, check if one exists per your directive. Only create new scripts if none exist.

2. **Self-anneal when things break.** Read error → fix script → test → update directive → log to `error-log.md`. If the fix uses paid tokens/credits, check with user first.

3. **Update directives as you learn.** Directives are living documents. When you discover API constraints, better approaches, or common errors — update the directive. Don't create/overwrite directives without asking unless told to.

4. **Verify before modifying external systems.** Before changing campaigns, deleting leads, or modifying any external state: sample the current state first to confirm the problem exists. Never bulk-modify based on assumptions.

5. **Ask before spending.** If any action might cost >$0.50 (API calls, scraping runs, LLM generations), confirm with the user first.

## Environment

- **Python 3.9** — use `Optional[X]` not `X | None` for type hints
- **AI calls via OpenRouter** (`OPENROUTER_API_KEY`), not the Anthropic SDK directly
- **Secrets in `.env`** (gitignored). Google OAuth: `credentials.json`, `token.json` (also gitignored)
- **Pre-commit hook** scans for key patterns (`AIzaSy`, `sk-`, `AKIA`, `ghp_`, `xai-`) and blocks commits

## Coding Standards

- `except Exception:` — never bare `except:`
- `os.getenv("KEY", "")` — never put real keys as default values
- Deserialize Supabase JSON at the data access layer (`isinstance` + `json.loads`)
- Clean output directories before file-generating scripts (prevent stale artifacts)
- Max ~6K output tokens per LLM call — split larger generations into parallel calls
- Always type-check API response fields before passing to `re.sub()` or `.get()`

## Cost Guardrails

- **Apify:** $0.50 max per pipeline run. Use server-side filters (`includeKeywords`, `budget`). One run with all keywords, not N runs with one keyword each.
- **LLM:** Split large generations into parallel calls with separate timeouts and retries.
- **General:** Ask user before any action that might exceed $0.50.

## Security

- All secrets in `.env` (gitignored). Never commit `.env`, `credentials.json`, or `token.json`.
- **Never** hardcode API keys in `os.getenv()` defaults or anywhere in source code.
- Pre-commit hook is a safety net, not a substitute for discipline.

## File Organization

**Directory structure:**
- `.tmp/` — Intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.
- `execution/` — Python scripts (deterministic tools)
- `directives/` — SOPs in Markdown (instruction set)
- `Example of Upwork Job/` — Approved Upwork job examples (see `upwork-auto-apply/CLAUDE.md`)
- `upwork-auto-apply/` — Upwork auto-apply pipeline

**Project organization:**
- Before new work, ask: "New project or part of an existing one?"
- New projects get a dedicated folder at workspace root. Ask user for the name.
- Never scatter project files loose in the root.
- Quick one-off tasks use `.tmp/` for intermediates.

**Deliverables** go to cloud services (Google Sheets, Slides). **Intermediates** stay local in `.tmp/`.

## Webhooks (Modal)

Event-driven execution via Modal. Each webhook maps to one directive with scoped tool access.

To add a webhook: follow `directives/add_webhook.md`. Key files: `execution/webhooks.json`, `execution/modal_webhook.py`.

Available tools for webhooks: `send_email`, `read_sheet`, `update_sheet`. All activity streams to Slack.

## Instantly API (Email Outreach)

**Local docs:** `execution/instantly_api_docs/` — 14 markdown files scraped from developer.instantly.ai. **Always check `execution/instantly_api_docs/README.md` before making any Instantly API call.**

**Auth:** Bearer token from `.env` (`INSTANTLY_API_KEY`). Header: `Authorization: Bearer <key>`.

**Critical rules (hard-won from production bugs):**

1. **PATCH doesn't reload the sending engine.** After PATCHing sequences on a running campaign, you MUST pause then activate (`POST /campaigns/{id}/pause`, then `POST /campaigns/{id}/activate`) to force the engine to pick up changes. Without this, the old settings continue running.

2. **Pause/activate endpoints need bare auth header.** Do NOT send `Content-Type: application/json` without a body — it returns 400. Use only `Authorization: Bearer <key>`.

3. **`daily_limit` is campaign-level, not per-account.** With N accounts at 30/day each, set `daily_limit: N × 30`. The default of 30 caps total sends regardless of how many accounts are attached.

4. **Leads API returns org-level data.** `POST /api/v2/leads/list` ignores `campaign_id` param. Filter client-side by `lead['campaign']` field.

5. **Analytics under-reports.** `/campaigns/analytics` `emails_sent_count` is unreliable. Use `/emails` endpoint and count by `from_address_email`.

6. **Email `body` is a dict, not string.** `{"html": "...", "text": "..."}` — always extract with `body.get("html") or body.get("text")`.

7. **Always include `delay_unit: "days"` on sequence steps.** Without it, Instantly defaults to minutes.

8. **`delay` on step N controls the gap before step N+1, NOT before the current step.** Step 0 delay = gap before Touch 2. Step 1 delay = gap before Touch 3. The last step's delay is irrelevant (no next step). Setting step 0 delay=0 causes Touch 2 to fire immediately (after only `email_gap` minutes).

9. **After any campaign change, verify delays by checking email timestamps on the first few leads within 24 hours.**

**Key files:**
- `execution/instantly_api_docs/README.md` — Quick reference (endpoints, schemas, status codes)
- `execution/instantly_api_docs/campaign.md` — Campaign CRUD, pause/activate
- `execution/instantly_api_docs/schemas.md` — Sequence step schema (delay, delay_unit, variants)
- `execution/instantly_api_docs/lead.md` — Lead CRUD and listing
- `execution/instantly_api_docs/email.md` — Email listing (sent, replies)
- `execution/run_outreach_campaign.py` — Campaign creation script (uses templates from `execution/campaign_templates/`)

## KIE API (ElevenLabs Proxy)

**Local docs:** `execution/kie_api_docs/` — API documentation for ElevenLabs models via KIE proxy. **Always check these docs before making any ElevenLabs API call.**

**Auth:** Bearer token from `.env` (`KIE_API_KEY`). Header: `Authorization: Bearer <key>`.

**Base URL:** `https://api.kie.ai`

**Models:**
- `elevenlabs/text-to-dialogue-v3` — TTS narration. Input: `{"dialogue": [{"text": "...", "voice": "Liam"}], "stability": 0.5, "language_code": "en"}`
- `elevenlabs/sound-effect-v2` — Sound effects. Input: `{"text": "prompt", "duration_seconds": 3.0}`

**Pattern:** Async task creation + polling:
1. `POST /api/v1/jobs/createTask` → returns `taskId`
2. `GET /api/v1/jobs/recordInfo?taskId=<id>` → poll every 3s until `state: "success"`
3. Parse `resultJson` → `resultUrls` array → download

**Reference script:** `execution/kie_gen_single.py` — working example of both narration and SFX generation.

**Key docs:**
- `execution/kie_api_docs/text-to-dialogue-v3.md` — Full TTS API reference
- `execution/kie_api_docs/sound-effect-v2.md` — Full SFX API reference

## Error Log

**The full error log lives in `error-log.md` at the workspace root.**

- **Before any task**, scan `error-log.md` for relevant entries.
- **After any error**, append an entry to `error-log.md` immediately after fixing it.
- **Periodically**, distill recurring patterns from `error-log.md` into this file's Coding Standards or Operating Principles sections, then tag the entry as `distilled-to-CLAUDE.md`.

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.
