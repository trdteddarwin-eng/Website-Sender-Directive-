# Ketka Landing Page — Session Handoff

Use this to onboard a new Claude session. Copy everything below into your first message.

---

## Copy-Paste Prompt for New Session

```
I'm working on the Ketka landing page at:
/Users/yoljean/Downloads/Ted Workspace/Ketka-lending-page.-/

Read the file Ketka-lending-page.-/SESSION_HANDOFF.md for full context, then read CLAUDE.md for workspace rules.

## What This Project Is

Tedca Corp landing page — a Vite + React + Tailwind CSS v4 site selling three AI services:
1. **AI Automation** — 6 automation cards (follow-up, lead scoring, chatbot, lead gen, email reply, WhatsApp) with flowchart modals
2. **AI Voice Receptionist** — 24/7 phone answering, appointment booking
3. **Agentic Workflows** — TikTok Video Creation + AI Outreach Pipeline with inline expand panels

## What Was Just Done (Latest Session — 2026-02-23)

### Phase 1: Automation Tab Cleanup + Agentic Workflow Enhancements

1. **Removed 4 automation cards** — auto-invoice, lead-nurturing, ai-proposal, auto-crm (HTML + FLOWCHART_DATA entries)
2. **Changed automation grid** from `md:grid-cols-4` → `md:grid-cols-3` (6 cards + Custom = 7 total)
3. **Added green "sold" badges** to all 6 automation cards:
   - WhatsApp: 312 | Lead Gen: 287 | Chatbot: 264 | Follow-Up: 241 | Lead Scoring: 198 | Email Reply: 176
   - CSS class: `.auto-sold-badge` — green (#34C759) pill, absolute top-right
4. **Added Website Email Pipeline card** to Agentic tab (replaced Coming Soon Card 1)
   - "AI Outreach Pipeline" with 4-step mini workflow (Research → Design → Review → Deploy)
   - Tech badges: Web Scraping, AI Design, Auto Deploy, Email Draft
5. **Added click-to-expand inline "How It Works"** for agentic workflow cards
   - `AGENTIC_DATA` object with `tiktok` (5 steps + 3 video embeds) and `website-pipeline` (4 steps)
   - `toggleAgenticExpand(cardId)` — toggles expand/collapse, switches content
   - `animateAgenticSteps()` — staggered reveal animation
   - CSS: `.agentic-expand-panel` (grid-row animation), `.agentic-step`, `.agentic-video-row`
6. **Copied 3 demo videos** to `videos/`:
   - `speedtolead.mp4` (4.6 MB), `greengrow-ai-automation.mp4` (1.7 MB), `greengrow-brand-hero.mp4` (1.1 MB)
   - Source: `yt-growth-chart/out/`

### Phase 2: Spline 3D Hero

7. **Replaced hero right-side service cards** with interactive Spline 3D scene
   - Uses `@splinetool/viewer` web component (v1.9.82 via unpkg CDN)
   - Scene URL: `https://prod.spline.design/pR4jr0vesEcOOm-r/scene.splinecode`
   - Container: 600px tall with negative margins for dramatic bleed effect
   - **Color-shifted** via CSS `filter: hue-rotate(160deg) saturate(1.3) brightness(1.05)` to match site red (#E63B2E) accent
   - **Locked in place** — `pointer-events: none` so mouse passes through (no drag/rotate)
   - **Spline watermark hidden** — CSS `::part(logo)`, cover element, and shadow DOM JS removal
   - Responsive: 400px on tablet, 320px on mobile

### Git State
- Both repos pushed and up to date:
  - **Main workspace:** https://github.com/trdteddarwin-eng/Website-Sender-Directive-.git (main branch)
  - **Ketka dedicated repo:** https://github.com/trdteddarwin-eng/Ketka-lending-page.-.git (main branch)
- `execution/smtp_accounts.json` intentionally NOT committed (contains real passwords)

## Page Structure (3 Tabs)

### Tab 1: AI Automation
- 6 automation cards + 1 "Request Custom" card in 3-column grid
- Each card has green "sold" badge + flowchart modal on click
- Flowchart modal: vertical pipeline with animated step-by-step reveal
- Automation FAQ section below

### Tab 2: AI Voice Receptionist
- Demo form, How It Works, Pain Points, Industry cards
- Human vs AI comparison, ROI calculator, Pricing

### Tab 3: Agentic Workflows
- TikTok Video Creation card (clickable → expands 5-step pipeline + 3 video embeds)
- AI Outreach Pipeline card (clickable → expands 4-step pipeline)
- Custom Workflows (Coming Soon) card
- Inline expand panel between cards and Book a Call button
- Pipeline Simulation engine (4 AI agents, 34s animation, auto-loops)

### Hero Section
- Left: Value prop headline + 3 CTA buttons (Automation, Voice AI, Agentic)
- Right: Spline 3D scene (color-shifted, non-interactive, animated)

## Tech Stack
- **Vite 6.4.1** — dev server
- **Tailwind CSS 4.2.0** — via `@tailwindcss/postcss`
- **React 19** — for the Gemini voice demo overlay (index.tsx)
- **@splinetool/viewer 1.9.82** — 3D scene in hero (CDN)
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
- `index.html` — The full landing page (~3975 lines, all HTML + inline CSS + inline JS)
- `index.css` — Tailwind v4 config + base styles
- `index.tsx` — React app for voice demo overlay
- `videos/` — 3 demo TikTok videos for agentic expand panel
- `postcss.config.js` — PostCSS with @tailwindcss/postcss
- `vite.config.ts` — Vite config with React plugin
- `constants.ts` — System instructions for the Gemini voice AI

## Known State
- All tabs switch correctly, flowchart modals open/close (X, Escape, backdrop)
- Agentic expand panels toggle on card click, collapse on re-click
- Spline 3D scene loads, animates, doesn't capture mouse
- Pipeline simulation auto-plays when scrolled into view
- Videos play inline with controls in TikTok expand section
- Sold badges render on all 6 automation cards

## What Might Need Work Next
- Mobile testing (375px, 414px, 768px viewports) — especially Spline scene sizing
- Verify Spline 3D color shift looks right on different monitors
- TikTok video expand → videos may need poster frames for faster perceived load
- Spline scene loading time — may want a skeleton/placeholder while it loads
- The Spline hue-rotate is approximate — if user gets a new Spline scene with correct colors, can remove the filter
```
