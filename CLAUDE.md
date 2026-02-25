# Agent Instructions

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- Basically just SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read `directives/scrape_website.md` and come up with inputs/outputs and then run `execution/scrape_single_site.py`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Environment variables, api tokens, etc are stored in `.env`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work.

**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

## New Project Detection

**Before starting any new work, always ask: "Is this a new project or part of an existing one?"**

- If the user says it's a **new project**, create a dedicated folder for it at the workspace root (e.g., `project-name/`) and keep all related files inside it. Ask the user what to name it.
- If it's **part of an existing project**, ask which project folder to work in and navigate there.
- **Never scatter project files loose in the workspace root.** Every project gets its own folder.
- If the user's request is a quick one-off task (not a project), use `.tmp/` for any intermediate files.

This keeps the workspace clean. The root should only contain: project folders, `execution/`, `directives/`, config files, and `CLAUDE.md`.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)
- Update the directive with what you learned (API limits, timing, edge cases)
- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

## Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: Google Sheets, Google Slides, or other cloud-based outputs that the user can access
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
- `.tmp/` - All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.
- `execution/` - Python scripts (the deterministic tools)
- `directives/` - SOPs in Markdown (the instruction set)
- `Example of Upwork Job/` - User-approved Upwork job examples (reference guide for auto-apply pipeline). **Read before every pipeline run.**
- `upwork-auto-apply/` - Upwork auto-apply pipeline (see `directives/upwork_auto_apply.md`)
- `.env` - Environment variables and API keys
- `credentials.json`, `token.json` - Google OAuth credentials (required files, in `.gitignore`)

**Key principle:** Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in `.tmp/` can be deleted and regenerated.

## Cloud Webhooks (Modal)

The system supports event-driven execution via Modal webhooks. Each webhook maps to exactly one directive with scoped tool access.

**When user says "add a webhook that...":**
1. Read `directives/add_webhook.md` for complete instructions
2. Create the directive file in `directives/`
3. Add entry to `execution/webhooks.json`
4. Deploy: `modal deploy execution/modal_webhook.py`
5. Test the endpoint

**Key files:**
- `execution/webhooks.json` - Webhook slug → directive mapping
- `execution/modal_webhook.py` - Modal app (do not modify unless necessary)
- `directives/add_webhook.md` - Complete setup guide

**Endpoints:**
- `https://nick-90891--claude-orchestrator-list-webhooks.modal.run` - List webhooks
- `https://nick-90891--claude-orchestrator-directive.modal.run?slug={slug}` - Execute directive
- `https://nick-90891--claude-orchestrator-test-email.modal.run` - Test email

**Available tools for webhooks:** `send_email`, `read_sheet`, `update_sheet`

**All webhook activity streams to Slack in real-time.**

## Upwork Auto-Apply — Job Reference Folder

**MANDATORY: Before every Upwork auto-apply pipeline run, read `Example of Upwork Job/`.**

This folder is the user's curated reference of approved Upwork jobs. It defines their taste, capabilities, and preferences. Every file in it is a job the user explicitly said "yes, let's do this" to.

**How to use it:**

1. **Before scoring (Phase 2):** Read all files in `Example of Upwork Job/` to understand what jobs the user likes — budget ranges, job types, skill requirements, client profiles. Use this to calibrate the AI classifier's relevance scoring. Jobs that match the patterns in this folder should score higher.

2. **Before applying (Phase 5):** Cross-reference scraped job URLs against this folder. If a job is already here, skip it (already applied or tracked).

3. **When user approves a job:** Any time the user says "yes", "let's do this", "apply to this one", or otherwise approves an Upwork job — **immediately add it to `Example of Upwork Job/`** as a markdown file named `YYYY-MM-DD_short-job-title.md`. Include: title, URL, budget, type, skills, description, and why it was a good fit.

4. **Pattern recognition:** Over time this folder builds a profile. Use it to answer: "What does a good job look like for this user?" If a scraped job is similar to 3+ examples in the folder, it's almost certainly a good fit. If it doesn't resemble anything in the folder, score it lower.

**File format:** See `Example of Upwork Job/README.md` for the template.

**Rule:** Never skip reading this folder before a pipeline run. It is the single source of truth for job preferences.

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

Also, use Opus-4.5 for everything while building. It came out a few days ago and is an order of magnitude better than Sonnet and other models. If you can't find it, look it up first.

## Error Log — Never Make the Same Mistake Twice

**This section is automatically maintained.** Every time you make a mistake, hit an error, or learn something the hard way, you MUST append an entry here immediately after fixing it. This is non-optional. The format:

```
### [YYYY-MM-DD] Short description of the mistake
- **What happened:** What went wrong
- **Why:** Root cause
- **Fix:** What you did to fix it
- **Rule:** The permanent rule to follow so this never happens again
```

**Before starting any task, scan this error log.** If a past mistake is relevant to what you're about to do, follow the rule. This is how the system gets smarter over time — you log it here, you read it next time, you don't repeat it.

---

### [2026-02-06] Higgsfield model path format wrong — kwaivgi vs kling-video
- **What happened:** `kwaivgi/kling-v2.6/motion-control` returned 404 on all variants
- **Why:** Higgsfield uses `kling-video` as the org prefix, not `kwaivgi` (which is Replicate's namespace). Format is `{org}/{version}/{tier}/{task}`.
- **Fix:** Changed to `kling-video/v3.0/pro/image-to-video`. Motion control = image-to-video with a `video_url` parameter.
- **Rule:** Higgsfield model paths: `kling-video/{version}/{pro|std}/{task}`. v2.6 uses `image_url`; v3.0 accepts both `image` and `image_url`. Always use `image_url` for consistency.

### [2026-02-06] Higgsfield upload API rejects video files
- **What happened:** `hf.upload_file("video.mp4")` and `hf.upload("bytes", "video/mp4")` both fail — only `image/*` and `audio/x-wav` are accepted.
- **Why:** Higgsfield's `/files/generate-upload-url` endpoint validates content_type to a whitelist of image/audio types.
- **Fix:** Upload videos to catbox.moe (`curl -F "reqtype=fileupload" -F "fileToUpload=@video.mp4" https://catbox.moe/user/api.php`) and pass the URL as `video_url`.
- **Rule:** Always use external hosting for video files with Higgsfield. Upload images via SDK, videos via catbox.moe or similar.

### [2026-02-06] Apify TikTok scraper searchSection needs leading slash
- **What happened:** `searchSection: "video"` caused validation error
- **Why:** Apify `clockworks/tiktok-scraper` requires `"/video"` with leading slash
- **Fix:** Changed to `"/video"` in scrape_tiktok_videos.py
- **Rule:** Always use `"/video"` (with leading slash) for Apify TikTok scraper searchSection

### [2026-02-06] MediaPipe 0.10.32+ removed solutions API
- **What happened:** `mediapipe.solutions.face_detection` throws AttributeError on v0.10.32
- **Why:** New MediaPipe removed legacy `solutions` namespace
- **Fix:** Pinned to `mediapipe==0.10.14`
- **Rule:** Use `mediapipe==0.10.14` for any code using `mp.solutions.face_detection`

### [2026-02-13] Switched from Higgsfield to KIE for Kling Motion Control
- **What happened:** Higgsfield account ran out of credits; also had a status-polling bug (`str(Status())` returns `"Completed()"` not `"completed"`)
- **Why:** Higgsfield SDK status types are class instances, not strings. Also, user preferred KIE (kie.ai) API which is cheaper.
- **Fix:** Rewrote `higgsfield_motion_control.py` to use KIE REST API. Upload via `https://kieai.redpandaai.co/api/file-stream-upload`, create task via `POST https://api.kie.ai/api/v1/jobs/createTask`, poll via `GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...`
- **Rule:** Use KIE API (not Higgsfield) for Kling. API key env var: `KIE_API_KEY`. Model: `kling-2.6/motion-control`. KIE result format uses `resultUrls` array. Avatar images must be <10MB (convert PNG→JPEG). KIE queue time can be 5-8 minutes — use 600s timeout minimum.

### [2026-02-13] KIE motion control rejects videos under 3 seconds
- **What happened:** Third segment (2.8s) from ffmpeg split failed with "Video duration must be between 3 and 30 seconds"
- **Why:** Kling 2.6 motion control requires reference video 3-30s. ffmpeg `-c copy` splits at keyframes, not exact times, so short remainder segments can fall below 3s.
- **Fix:** Accepted 2/3 segments (20s of 23s video). For future: use `-segment_time 15` for 23s videos to avoid short remainders, or re-encode with exact splits.
- **Rule:** Ensure all video segments are ≥3s for KIE motion control. Adjust segment_duration to avoid short last segments.

### [2026-02-13] Stale segment files from prior runs cause phantom segments
- **What happened:** Re-running `split_video()` with a different `segment_duration` picked up leftover segment files from the prior run (e.g., old `seg_002.mp4` from a 10s split persisted when re-running with 12s segments)
- **Why:** `split_video()` lists all matching `{base}_seg_*.mp4` files in the output dir, including stale ones from prior runs. ffmpeg `-y` overwrites seg_000/001 but doesn't delete seg_002 if the new split produces fewer segments.
- **Fix:** Added cleanup step in `split_video()` that removes all `{base}_seg_*.mp4` files from the output dir before splitting.
- **Rule:** Always clean the output directory of matching segment files before running ffmpeg segment split.

### [2026-02-16] Bright Data MCP SSE parsing: iter_lines() breaks multi-line JSON
- **What happened:** `requests.iter_lines()` splits SSE data on internal newlines, creating incomplete JSON fragments that fail to parse
- **Why:** Bright Data MCP sends large JSON in SSE `data:` fields. The markdown text inside the JSON contains `\n` characters. `iter_lines()` splits on those, so one SSE event becomes many lines — only the first has `data: ` prefix.
- **Fix:** Replaced `iter_lines()` with `iter_content(chunk_size=4096)` and a manual SSE parser that buffers until `\n\n` (event boundary), then extracts `data:` lines and joins them.
- **Rule:** Never use `iter_lines()` for SSE streams with large payloads. Always buffer with `iter_content()` and split on `\n\n` event boundaries.

### [2026-02-16] Bare `except:` catches SystemExit from sys.exit()
- **What happened:** `sys.exit(0)` inside a `try/except:` block was silently caught, preventing process exit
- **Why:** `SystemExit` inherits from `BaseException`. Bare `except:` catches `BaseException` subclasses including `SystemExit` and `KeyboardInterrupt`.
- **Fix:** Changed `except:` to `except Exception:`. Also use `os._exit(0)` for hard exits in subprocess scripts.
- **Rule:** Never use bare `except:` — always use `except Exception:`. Use `os._exit()` for subprocess scripts that need guaranteed exit.

### [2026-02-16] Bright Data MCP markdown scrape can't extract client metadata
- **What happened:** `payment_verified`, `total_spent`, `total_hires` always return false/0 from markdown scraping
- **Why:** Upwork search results page markdown doesn't include client payment/spending details — those require authenticated scraping or individual job page scraping.
- **Fix:** Disabled `verified_payment` and `min_client_spent` filters in pipeline config.
- **Rule:** MCP `scrape_as_markdown` only extracts what's visible on the page. For Upwork search, client metadata (payment verified, spend, hires) is NOT available. Only filter on: budget, experience level, proposals count, and skills.

### [2026-02-17] Spec site pipeline: all 5 sites look identical (same colors/layout)
- **What happened:** When running the spec site pipeline on 5 leads in parallel, all 5 agents produced nearly identical sites — same navy (#0B1D3A) / amber (#D4922A) color scheme, same section order, same layout structure.
- **Why:** The directive and prompt both hardcode the exact color values and section order. Parallel agents all follow the same spec literally, producing cookie-cutter output.
- **Fix:** Not yet fixed. Need to add variety instructions.
- **Rule:** When building spec sites in batch, vary the design per lead. Rotate between 3-4 color palettes (e.g., navy/amber, forest green/gold, charcoal/red, deep blue/orange). Vary section order and hero styles. The directive should include a palette rotation or let the agent pick based on lead # modulo. Each site should feel custom, not templated.

### [2026-02-17] Spec site screenshots blank below hero due to scroll-reveal animations
- **What happened:** new-site.png screenshots showed hero section but rest of page was blank/white
- **Why:** Agents added CSS scroll-reveal animations (.reveal { opacity: 0 }) triggered by IntersectionObserver on scroll. Playwright takes static screenshots without scrolling, so animated sections stay invisible.
- **Fix:** Added JS injection to screenshot_website.py that forces all .reveal elements visible before capture. Also: directive updated to warn agents not to use scroll-triggered opacity animations in spec sites.
- **Rule:** In screenshot_website.py, always force-reveal hidden animated elements before capturing. In spec site builds, never use opacity:0 scroll animations — use CSS-only animations (e.g., fade on page load) or skip animations entirely since the site is for screenshot/demo purposes.

### [2026-02-19] Lead detail page crashes: 'str object' has no attribute 'items'
- **What happened:** Every lead detail page returned 500 error
- **Why:** `lead.raw_data` is stored as a JSON string in Supabase, not a dict. Jinja2's `{% for key, val in lead.raw_data.items() if lead.raw_data is mapping %}` evaluates `.items()` BEFORE the `if` filter (the `if` in a for-loop is a post-filter, not a pre-condition).
- **Fix:** Changed outer `{% if %}` to `{% if lead.raw_data and lead.raw_data is mapping %}` so the check runs before iteration.
- **Rule:** Never use `if` filters inside Jinja2 `{% for %}` loops to guard against type errors. Always wrap the entire for-loop in a separate `{% if %}` block that validates the type first.

### [2026-02-19] Pipeline page stuck — all agents show IDLE after running
- **What happened:** After clicking "Run Next Lead", pipeline page shows all 4 agents as IDLE/Waiting forever, even though the pipeline thread is running.
- **Why:** SSE events published before the browser's EventSource connects are lost (no replay buffer). The pipeline thread starts immediately on POST and publishes events within milliseconds, but the browser takes 1+ seconds to navigate to /pipeline and establish the SSE connection.
- **Fix:** Added a 5-second DB polling fallback in pipeline.html that fetches `/api/pipeline/status` and updates agent cards from the database state, catching any missed SSE events.
- **Rule:** Never rely solely on SSE for critical UI state. Always add a polling fallback that hydrates from the database. SSE is for real-time feel; DB polling is for reliability.

### [2026-02-19] Pipeline crashes: 'str' object has no attribute 'get' on agents field
- **What happened:** Every pipeline run immediately fails with `'str' object has no attribute 'get'`
- **Why:** `create_pipeline_run` stores `agents` and `log` as `json.dumps(...)` strings. When `get_pipeline_run` reads them back from Supabase, the columns come back as JSON strings (not dicts). `_update_agent()` then calls `.get()` on the string, which fails.
- **Fix:** Added `_parse_run_json()` helper in `supabase_client.py` that auto-parses `agents` and `log` from JSON strings to dicts/lists. Applied to `get_pipeline_run`, `get_active_pipeline_run`, and `get_recent_pipeline_runs`.
- **Rule:** Always deserialize JSONB/text columns at the data access layer. Never assume Supabase returns parsed objects for JSON-stored fields — always check `isinstance(val, str)` and `json.loads()` at read time.

### [2026-02-19] Pipeline judge step crashes: PGRST204 missing columns + stale work dir
- **What happened:** Judge phase fails with `Could not find the 'judge_struct_score' column of 'pipeline_runs'`. Designer phase also completes instantly (0 seconds) because it finds stale `index.html` from a prior run.
- **Why:** `_run_judge()` tried to write `judge_struct_score`, `judge_visual_score`, `judge_visual_recommendation` directly to `pipeline_runs` table, but those columns don't exist in Supabase. Also, the work dir (`.tmp/{slug}/`) persists between runs, so `if not os.path.exists(html_out)` skips generation.
- **Fix:** Moved judge detail fields into the `agents` JSONB (under `judge` key). Added `shutil.rmtree(work_dir)` at the start of `run()` to clear stale artifacts before each pipeline run.
- **Rule:** Never write arbitrary columns to Supabase — only use columns that exist in the schema. Store extra metadata in JSONB fields (`agents`, `log`). Always clear the work directory at pipeline start to prevent stale file skips.

### [2026-02-19] Designer timeout: subprocess kills script before HTTP timeout fires
- **What happened:** Designer step fails every time with "Generation failed: Timeout after 120s". The `generate_spec_site.py` script calls OpenRouter's kimi-k2.5 model for 16K max tokens, which routinely takes 2-3 minutes.
- **Why:** Both the subprocess timeout in `pipeline_runner.py` and the HTTP request timeout in `generate_spec_site.py` were set to exactly 120s. They race each other, and the subprocess kill fires before the script can catch its own timeout and print a useful error.
- **Fix:** Rewrote `generate_spec_site.py` to split the site into 3 parallel API calls (top/middle/bottom sections, ~5K tokens each) instead of 1 monolithic 16K-token call. Each call has 180s timeout with 1 retry. CSS framework is Python-generated (deterministic). Subprocess timeout stays at 480s. Total wall time drops from 5-8 min to ~60-90s.
- **Rule:** Never ask kimi-k2.5 (or similar slow models) for >6K output tokens in a single call. Split large generations into parallel sections with a shared CSS framework. Each section gets its own API call with its own timeout and retry. Deterministic parts (CSS, document structure) should be Python-generated, not LLM-generated.

### [2026-02-23] Apify: 9 runs at $0.15 each = $1.35 blown on one pipeline execution
- **What happened:** Pipeline looped through 9 keywords, each launching a separate Apify scrape ($0.15/run), fetching 50 random jobs per run, then keyword-filtering locally. 95% of jobs were thrown away.
- **Why:** `scrape_upwork_jobs()` only passed `limit`/`fromDate`/`toDate`. The actor actually supports `includeKeywords`, `budget`, `vendor.experienceLevel`, and `connectsPrice` for server-side filtering — but the code never used them.
- **Fix:** Rewrote to send ALL keywords + filters in ONE Apify run. Server-side filtering returns only relevant jobs. Cost: ~$0.15 total vs $1.35.
- **Rule:** **Apify budget: $0.50 max per pipeline run.** Always use server-side `includeKeywords` and `budget` filters — never scrape generically then filter locally. One run with all keywords, not N runs with one keyword each.

### [2026-02-23] Python 3.9: `dict | None` type hints crash on import
- **What happened:** `flowchart_generator.py`, `applier.py`, `session_manager.py` all used `-> dict | None` type hints which crash Python 3.9 with `TypeError: unsupported operand type(s) for |`
- **Why:** PEP 604 union syntax (`X | Y`) requires Python 3.10+. This Mac runs Python 3.9.
- **Fix:** Changed all `X | None` to `Optional[X]` from `typing` module.
- **Rule:** Always use `Optional[X]` instead of `X | None` for type hints. Target Python 3.9 compatibility.

### [2026-02-23] Anthropic API key in .env is a placeholder
- **What happened:** Classifier returned 401 auth errors for all jobs.
- **Why:** `.env` line 5 contains `ANTHROPIC_API_KEY=PASTE_YOUR_ANTHROPIC_API_KEY_HERE` — a literal placeholder, not a real key.
- **Fix:** Switched classifier to use OpenRouter API (key is valid). Updated `classifier.py` to use `requests` + OpenRouter instead of `anthropic` SDK.
- **Rule:** All AI scoring/classification uses OpenRouter (`OPENROUTER_API_KEY`), not the Anthropic SDK directly. This avoids the missing Anthropic key issue.

### [2026-02-25] Google API key leaked via hardcoded fallback in os.getenv()
- **What happened:** Google flagged the API key as leaked with `PERMISSION_DENIED: Your API key was reported as leaked`. Gemini TTS calls failed.
- **Why:** `generate_ads_music.py` and `generate_background_music.py` used `os.getenv("GOOGLE_API_KEY", "AIzaSy...")` with the real key as the default fallback. These files were committed and pushed to a public GitHub repo. Google scans public repos and auto-revokes leaked keys.
- **Fix:** Removed hardcoded keys from both files (replaced with empty string fallback). Added a pre-commit git hook (`.git/hooks/pre-commit`) that scans staged files for API key patterns (`AIzaSy`, `sk-`, `AKIA`, `ghp_`, `xai-`) and blocks the commit.
- **Rule:** **NEVER put API keys as default values in `os.getenv()`.** Always use `os.getenv("KEY_NAME", "")`. All secrets live in `.env` (gitignored). The pre-commit hook will catch violations, but don't rely on it — just never hardcode keys.