# Ketka Landing Page — Session Handoff

Use this to onboard a new Claude session. Copy everything below into your first message.

---

## Copy-Paste Prompt for New Session

```
I'm working on the Ketka landing page at:
/Users/yoljean/Downloads/Ted Workspace/Ketka-lending-page.-/

Read the file Ketka-lending-page.-/SESSION_HANDOFF.md for full context, then read CLAUDE.md for workspace rules.

## What This Project Is

Tedca Corp landing page — a Vite + React + Tailwind CSS v4 site selling two AI services:
1. **AI Voice Receptionist** — 24/7 phone answering, appointment booking
2. **AI Automation Pipeline** — 4 AI agents (Researcher → Designer → Judge → Ops) that automate outreach

## What Was Just Done (This Session)

Restructured the entire landing page from a single-service (voice only) page to a dual-service page. Here's what changed:

### New Page Structure (20 sections, ~3021 lines)
1. Urgency Banner (updated — mentions both services)
2. Navbar (updated — added "Services" link, "Book a Call" CTA)
3. **NEW: Company Hero** — "AI Systems that run your business while you sleep" + dual CTAs + split visual
4. **NEW: Services Overview** — Two side-by-side cards (Voice Receptionist | AI Automation)
5. Social Proof (kept as-is)
6. **NEW: Service 1 Anchor** — dark bar "Service 01 — AI Voice Receptionist"
7. **NEW: Relocated Demo Form** — moved from old hero into its own section under Voice
8. How It Works (kept — scoped under Voice)
9. Pain Points (kept — scoped under Voice)
10. **NEW: Service 2 Anchor** — dark bar "Service 02 — AI Automation Pipeline"
11. **NEW: Pipeline Simulation** — animated dashboard showing 4 agents processing a lead in real-time (~34s animation, auto-plays on scroll via IntersectionObserver, loops with 3s pause)
12. **NEW: Automation Benefits** — 3 cards (Personalized at Scale, Deployed in Minutes, 4 AI Agents)
13. Integrations (kept)
14. Human vs AI Comparison (kept)
15. Timeline (kept, updated text)
16. ROI Calculator (kept)
17. Pricing (updated — tabbed: Voice AI plans | Automation plans)
18. Book a Call (kept — Cal.com embed)
19. FAQ (updated — added 4 automation questions)
20. Footer + Sticky CTA (updated copy)

### Pipeline Simulation Details
- Vanilla JS engine (no GSAP) — ~200 lines in a self-executing function
- Declarative TIMELINE array with 24 steps across 4 phases
- Agent cards: 2x2 grid with Idle → Working (red pulse) → Done (green) states
- Activity log: color-coded by agent, auto-scrolls
- Output bar slides up on completion
- IntersectionObserver at 30% threshold triggers auto-play
- Pauses when scrolled out of view, restarts when visible again

### Tailwind v4 Migration (Fixed)
- `postcss.config.js` updated: `tailwindcss` → `@tailwindcss/postcss`
- `index.css` rewritten: `@tailwind base/components/utilities` → `@import "tailwindcss"` + `@theme { }` block
- Custom colors (paper, signal, offwhite, dark, success) defined in `@theme`
- Custom fonts (heading, drama, mono, sans) defined in `@theme`
- Custom animations (fadeInUp, fadeIn, scaleIn, shimmer, float) defined in `@theme`

## Tech Stack
- **Vite 6.4.1** — dev server
- **Tailwind CSS 4.2.0** — via `@tailwindcss/postcss`
- **React 19** — for the Gemini voice demo overlay (index.tsx)
- **Font Awesome 6.4** — icons (CDN)
- **Google Fonts** — Space Grotesk, DM Serif Display, Space Mono, Inter
- **Cal.com** — embedded booking widget

## Dev Server
```bash
cd "/Users/yoljean/Downloads/Ted Workspace/Ketka-lending-page.-"
npx vite --host
# Runs on http://localhost:3001/ (or next available port)
```

## Key Files
- `index.html` — The full landing page (~3021 lines, all HTML + inline CSS + inline JS)
- `index.css` — Tailwind v4 config + base styles
- `index.tsx` — React app for voice demo overlay
- `postcss.config.js` — PostCSS with @tailwindcss/postcss
- `tailwind.config.ts` — OLD format (not used by TW v4, kept for reference)
- `vite.config.ts` — Vite config with React plugin
- `constants.ts` — System instructions for the Gemini voice AI

## Known State
- All internal anchor links verified (6 anchors, all resolve)
- HTML structure validated (no unclosed tags)
- Vite serves cleanly with no build errors
- The page was loading at localhost:3001 when session ended

## What Might Need Work Next
- Mobile testing (375px, 414px, 768px viewports)
- Pipeline simulation polish (timing tweaks, mobile layout)
- Verify demo form still triggers React overlay in new location
- Spotlight card mouse-follow effect may need pointer-events check
- Performance check on pipeline animation (setTimeout chains)
```
