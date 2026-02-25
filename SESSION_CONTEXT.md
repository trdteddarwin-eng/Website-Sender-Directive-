# Ted Workspace — Session Context

**Last updated:** 2026-02-25
**Workspace:** `/Users/yoljean/Downloads/Ted Workspace/`

Read `CLAUDE.md` first for system-wide instructions (3-layer architecture, error log, operating principles), then this file for project state.

---

## What This Is

This is Ted's (Tedca Corp) multi-project workspace for AI-powered business tools. The workspace contains several interconnected projects: a Flask-based HVAC lead outreach pipeline (TedCA Dashboard), a Remotion-based short-form video production system (yt-growth-chart), an Upwork auto-apply pipeline, and a landing page (Ketka). The business sells AI automation, voice receptionist, and agentic workflow services to small businesses. Videos are marketing content for TikTok/Reels to drive inbound leads.

---

## Architecture

**3-Layer System** (defined in `CLAUDE.md`):
- **Directives** (`directives/`) — SOPs in Markdown. Living documents that get updated as we learn.
- **Orchestration** — Claude reads directives, makes decisions, calls execution scripts, handles errors.
- **Execution** (`execution/`) — 80+ deterministic Python scripts for API calls, data processing, file ops.

Why: LLMs are probabilistic but business logic is deterministic. Pushing complexity into scripts makes the system reliable. 90% accuracy per LLM step = 59% over 5 steps. Scripts fix that.

---

## Codebase Map

```
/Users/yoljean/Downloads/Ted Workspace/
├── CLAUDE.md                          # Agent instructions + error log (READ FIRST)
├── SESSION_CONTEXT.md                 # This file
├── .env                               # All API keys (never commit)
│
├── yt-growth-chart/                   # Remotion video production
│   ├── src/
│   │   ├── Root.tsx                   # All compositions registered here
│   │   ├── RAGAgent.tsx               # RAG Agent video — 12 scenes, 60fps, directional wipe transitions (~800 lines)
│   │   ├── VoiceReceptionist.tsx      # Voice receptionist video
│   │   ├── ChillGym.tsx              # ChillGym video
│   │   └── ...                        # Other video compositions
│   ├── public/
│   │   ├── narration-ragagent/        # 12 ElevenLabs TTS clips (scene_00-11.mp3)
│   │   ├── sfx-ragagent/             # 12 SFX clips (sfx_00-11.wav)
│   │   └── ...                        # Other video assets
│   ├── out/                           # Rendered MP4s
│   │   ├── ragagent.mp4              # Latest render (60fps, 5.2MB, directional wipe transitions)
│   │   ├── agentic.mp4, chatbot.mp4, receptionist.mp4, etc.
│   └── package.json                   # Remotion 4.0.421, React 19
│
├── execution/                         # Python scripts (the tools)
│   ├── generate_ragagent_narration.py # ElevenLabs TTS for RAG Agent (12 scenes)
│   ├── generate_ragagent_sfx.py       # SFX generation
│   ├── generate_*_narration.py        # Narration for other videos
│   ├── generate_*_sfx.py             # SFX for other videos
│   ├── upwork_apify_scraper.py        # Upwork job scraping
│   └── ...                            # 80+ other scripts
│
├── pipeline-app/                      # Flask HVAC lead outreach dashboard
│   ├── app.py                         # Entry point (port 5050)
│   ├── schema.sql                     # Full Supabase schema
│   ├── services/
│   │   ├── supabase_client.py         # Data layer — ALL DB operations
│   │   ├── pipeline_runner.py         # 4-phase pipeline (researcher→designer→judge→ops)
│   │   ├── smtp_sender.py            # Email via @tedca.online SMTP
│   │   └── ...
│   ├── blueprints/                    # Flask routes
│   └── templates/                     # Jinja2 HTML
│
├── directives/                        # SOPs in Markdown
├── upwork-auto-apply/                 # Upwork job application pipeline
├── Ketka-lending-page.-/              # Landing page (Vite + React + Tailwind)
├── Example of Upwork Job/             # Approved job reference (read before pipeline runs)
└── .tmp/                              # Intermediate files (regeneratable)
```

---

## Tech Stack & Environment

| Component | Details |
|-----------|---------|
| Video Framework | Remotion 4.0.421, React 19, TypeScript |
| TTS | ElevenLabs API, multilingual_v2 model, custom cloned voice (ID: `yj30vwTGJxSHezdAGsv9`) |
| AI Models | OpenRouter API (NOT Anthropic SDK directly — key is placeholder). Use Opus-4.5 when building. |
| Pipeline Dashboard | Flask + Jinja2 + vanilla JS, SSE for live updates |
| Database | Supabase (Postgres) via supabase-py |
| Email | SMTP via @tedca.online accounts (NOT Gmail API) |
| Hosting | Netlify (spec sites), Modal (webhooks) |
| Language | Python 3.9 (Mac default), TypeScript/Node |
| Package Manager | npm (yt-growth-chart), pip (execution scripts) |

**Env vars needed:** `OPENROUTER_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `NETLIFY_TOKEN`, `KIE_API_KEY`, `APIFY_TOKEN`

**Compatibility notes:**
- Python 3.9 — use `Optional[X]` not `X | None` (PEP 604 needs 3.10+)
- `mediapipe==0.10.14` (newer versions removed `solutions` API)
- All AI scoring/classification uses OpenRouter, not Anthropic SDK (key is placeholder)

---

## Session History

### 2026-02-20 — Pipeline Dashboard Enhancements

1. **Compose Email from Drafts Page** — Compose button + modal on `/drafts`, `POST /api/emails/compose`
2. **Run Specific Lead** — Search modal with typeahead, `GET /api/leads/search?q=...`
3. **Pipeline Resume/Retry** — `POST /api/pipeline/resume` resumes from failure point
4. **Pipeline State Persistence** — Page reload restores agent cards from Supabase
5. **Schema Fix** — `email_sequences.sender_account` was missing, crashed OPS step. Fixed via ALTER TABLE.

### 2026-02-25 — RAG Agent Video: Voice Tuning, Professional Transitions, 60fps

1. **Voice tuning — make narration sound human**
   - What: Changed ElevenLabs voice settings in `execution/generate_ragagent_narration.py` line 51-54
   - Values: stability 0.80→0.45, similarity_boost 0.75→0.80, style 0.1→0.40
   - Why: Voice sounded robotic/monotone. Lower stability = natural pitch variation. Higher style = expressive emphasis. Reference: chatbot/agentic videos use 0.6/0.3 and sound better, we pushed further for short-form energy.
   - Deleted all 12 clips in `yt-growth-chart/public/narration-ragagent/`, regenerated all 12 successfully
   - Files: `execution/generate_ragagent_narration.py`

2. **Added professional directional wipe transitions**
   - What: Replaced simple back-to-back scene cuts with directional wipe + leading edge glow
   - Did deep research (DeepSeek) on how professional motion designers do transitions
   - Key learnings: staggered element choreography (3-7 frame delays), directional movement, custom easing curves, leading edge effects
   - Implementation in `yt-growth-chart/src/RAGAgent.tsx`:
     - `DirectionalWipePresentation` — clip-path inset wipe with glowing white edge line
     - Alternating LTR/RTL between transitions for visual rhythm
     - Exiting scene shifts in wipe direction (-40px) + scales to 0.96 + fades
     - `GraphicExitWrap` component — graphics scale to 0.88 + fade in last 18 frames of each scene
     - `TextBlock` upgraded — slides up from +25px on enter, slides to -30px on exit (not just opacity)
     - Easing: `Easing.out(Easing.poly(4))` — fast decisive start, smooth deceleration
     - Transition overlap: 18 frames (0.6s)
   - REJECTED: Simple zoom-fade (cinematicZoom) — tried first, looked amateur. Whole scene fades as a blob.
   - Files: `yt-growth-chart/src/RAGAgent.tsx`, `yt-growth-chart/src/Root.tsx`

3. **Upgraded to native 60fps**
   - What: Full fps-independent refactoring of all 12 graphic components + TextBlock + GraphicExitWrap + SceneWrapper
   - Approach: Added `const f = frame * 30 / fps` normalization in every component. All existing frame math uses `f` (30fps-equivalent) so animation timing is identical at any fps. Springs use `spring({ frame: f, fps: 30, config })`.
   - Main composition dynamically computes durations: `Math.round(SD * fps / 30)`
   - Audio volume callbacks also normalized: `rawF * 30 / fps`
   - Root.tsx: fps 30→60, durationInFrames 1182→2364
   - REJECTED: ffmpeg motion interpolation — clean SVG line art + text needs native rendering, interpolation causes ghosting artifacts
   - TypeScript type-checks clean. Rendered successfully: 2364 frames, 5.2MB
   - Files: `yt-growth-chart/src/RAGAgent.tsx` (full rewrite), `yt-growth-chart/src/Root.tsx`

4. **Created /save-session skill**
   - Context engineering tool for session handoffs
   - Captures full mental model, not just file changes
   - `.claude/skills/save-session/SKILL.md`

---

## Current State

### What's Working
- **RAG Agent video** — Fully rendered at 60fps with directional wipe transitions, 12 scenes with narration + SFX. Output: `yt-growth-chart/out/ragagent.mp4` (5.2MB, 1080x1920, ~39s)
- **All 12 narration clips** — Regenerated with human-sounding voice settings. In `yt-growth-chart/public/narration-ragagent/`
- **Remotion Studio** — Was running at localhost:3002 (may need restart: `cd yt-growth-chart && npx remotion studio`)
- **TedCA Pipeline Dashboard** — Working at localhost:5050. Pipeline, email sequences, drafts all functional.
- **Other videos** — agentic.mp4, chatbot.mp4, receptionist.mp4, chillgym.mp4 all previously rendered in `yt-growth-chart/out/`

### What's In Progress
- RAG Agent video may need further transition refinement based on user review
- User was previewing the 60fps render when session was saved

### What's Broken / Known Issues
1. **Email open/click/bounce tracking** — `open_count` column exists but never updates. No tracking pixel.
2. **Spec site analytics** — No way to know if leads visit deployed sites.
3. **`.env` line 35** — `password for email=...` causes python-dotenv parse warning. Harmless but noisy.
4. **Anthropic API key** — Placeholder in `.env`. All AI uses OpenRouter instead.

---

## Key Decisions & Reasoning

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Voice settings (RAG Agent) | stability=0.45, similarity_boost=0.80, style=0.40 | 0.80/0.75/0.1 (original) | Original was monotone/robotic. Lower stability = natural pitch variation. Higher style = conversational energy. Pushed further than chatbot (0.6/0.3) for short-form. |
| Transition type | Directional wipe + glow edge line | Zoom-fade (tried first) | Deep research showed: wipes look professional, staggered element exits add polish, glow line on black bg looks premium. Zoom-fade was "everything moves at once" = amateur. |
| Wipe direction | Alternating LTR/RTL | Always same | Creates visual rhythm, prevents repetition fatigue |
| 60fps implementation | Native normalization (`f = frame * 30 / fps`) | ffmpeg interpolation, doubling all constants | Normalization preserves all original timing math, works at ANY fps. ffmpeg causes artifacts on clean SVG. Doubling constants is error-prone. |
| Easing curve | `Easing.out(Easing.poly(4))` | linear, ease-in-out, cubic | Poly(4) ease-out = fast decisive start + smooth deceleration. Feels "confident" — like the wipe knows where it's going. |
| AI API | OpenRouter (all models) | Anthropic SDK direct | Anthropic key in .env is a placeholder. OpenRouter key is valid. Avoid the missing key issue. |
| Voice clone | ElevenLabs `eleven_multilingual_v2` | — | User's custom cloned voice. Voice ID: `yj30vwTGJxSHezdAGsv9` |

---

## User Preferences

- **Action-oriented** — Prefers "just do it" over lengthy discussion. Plans are OK but should be brief.
- **Professional quality bar** — Pushes for things to look like "a professional would do it." Not satisfied with basic/default implementations.
- **Research-informed** — Uses deep research (DeepSeek) to learn best practices before implementing. Wants to understand the craft.
- **Context engineering** — Values comprehensive session handoffs. Wants new sessions to be immediately productive.
- **Voice-to-text input** — Sometimes has transcription artifacts (e.g., "soup form" = "swipe form"). Interpret intent, don't get stuck on exact wording.
- **Tool preferences** — OpenRouter for AI, ElevenLabs for TTS, Remotion for video, Supabase for data.
- **Model preference** — Use Opus-4.5 for everything while building (stated in CLAUDE.md).
- **Communication** — Brief, direct. Says "play it again" or "can you make it 60fps or no?" — expects action, not explanation.

---

## How to Run

```bash
# Remotion Studio (video preview)
cd "/Users/yoljean/Downloads/Ted Workspace/yt-growth-chart"
npx remotion studio
# → http://localhost:3002

# Render RAG Agent video
cd "/Users/yoljean/Downloads/Ted Workspace/yt-growth-chart"
npx remotion render RAGAgent out/ragagent.mp4 --codec=h264

# Regenerate narration (needs ELEVENLABS_API_KEY)
cd "/Users/yoljean/Downloads/Ted Workspace"
export $(grep -v '^#' .env | xargs) && python3 execution/generate_ragagent_narration.py

# TedCA Pipeline Dashboard
cd "/Users/yoljean/Downloads/Ted Workspace/pipeline-app"
python3 app.py
# → http://localhost:5050
```

---

## Data Layer (TedCA Pipeline)

**Database:** Supabase (Postgres) via `supabase-py` REST client.

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

---

## Git State

- **Branch:** `main`
- **Remote:** `https://github.com/trdteddarwin-eng/Website-Sender-Directive-.git`
- **Last commit:** `750c9fe` — Landing page overhaul: trim automation cards, add Spline 3D hero, agentic workflow expand
- **Uncommitted changes:** RAGAgent.tsx (transitions + 60fps), Root.tsx (fps=60), generate_ragagent_narration.py (voice settings), regenerated narration clips, rendered ragagent.mp4, save-session skill, plus many other modified/untracked files from prior work

---

## What's Next

- User was reviewing the 60fps RAG Agent video with directional wipe transitions
- May want to iterate on transition style, add more polish, or try different transition types
- Could export final video for TikTok/Reels upload
- Other videos (chatbot, agentic, receptionist, chillgym) may need similar transition + 60fps treatment
- The video is marketing content for Tedca Corp's AI services

---

## Prompt for New Claude Session

Copy and paste this:

```
I'm working in the Ted Workspace at `/Users/yoljean/Downloads/Ted Workspace/`. Read `CLAUDE.md` first (3-layer architecture, error log, operating principles), then read `SESSION_CONTEXT.md` for full project state.

This workspace has multiple projects. The active one is `yt-growth-chart/` — a Remotion 4.0.421 video production system that renders short-form vertical videos (1080x1920) for TikTok/Reels marketing. The videos sell AI automation services (Tedca Corp).

Last session (Feb 25) we worked on the RAG Agent video (`src/RAGAgent.tsx`): tuned ElevenLabs voice settings to sound human (stability=0.45, style=0.40 — lower = more natural), added professional directional wipe transitions with a glowing white edge line (alternating LTR/RTL, staggered element exits, custom poly(4) ease-out), and upgraded to native 60fps via frame normalization (`f = frame * 30 / fps` in all 12 components). The rendered output is `out/ragagent.mp4` (60fps, 5.2MB, ~39s). Remotion Studio runs on localhost:3002.

Key technical notes: Python 3.9 (use Optional[X] not X|None), all AI uses OpenRouter (not Anthropic SDK — key is placeholder), ElevenLabs voice ID is yj30vwTGJxSHezdAGsv9, narration clips are in public/narration-ragagent/. The other major project is `pipeline-app/` — a Flask HVAC lead outreach dashboard at localhost:5050 with Supabase backend.

I prefer action over discussion, push for professional quality, and use deep research when learning new techniques. Interpret voice-to-text transcription loosely — focus on intent. Use Opus-4.5 for everything.
```
