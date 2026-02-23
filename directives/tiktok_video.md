# Directive: TikTok Video Creation

## Goal
Create a 15-scene TikTok-style Remotion video on any given topic. User just says the topic — this directive handles everything from script to rendered MP4.

## Trigger
"Make a TikTok video about [topic]" or "Create a video about [topic]"

## Inputs
- **Topic**: What the video is about (e.g., "AI email automation", "why ads matter", "voice receptionist")
- **Angle** (optional): Specific messaging angle. If not provided, default to: problem → stats → solution → CTA
- **CTA keyword** (optional): The DM keyword (e.g., "email", "ads", "receptionist"). If not provided, derive from topic.

## Architecture
All videos follow the same proven structure from `AIAutomation.tsx`:
- **15 scenes**, 70 frames each (~2.33s per scene at 30fps)
- **TransitionSeries** with 10-frame fade transitions
- **Total duration**: 1190 frames (~39.7s)
- **Resolution**: 1080x1920 (TikTok vertical)
- **Audio**: Per-scene narration (ElevenLabs TTS) + per-scene SFX (Replicate AudioGen, ~$0.012/scene)
- **Brand colors**: RED `#FF3B3B`, GREEN `#4ADE80`, ACCENT `#FBBF24`, BLUE `#60A5FA`

## Scene Script Formula
Every video follows this arc:

| Scenes | Purpose | Color Tone |
|--------|---------|------------|
| 0-1 | **Hook** — Identify the problem, create urgency | RED |
| 2-4 | **Pain** — Stats, consequences, what they're losing | RED |
| 5-6 | **Shift** — Introduce the solution | GREEN transition |
| 7-9 | **Proof** — How it works, specific benefits, ROI | GREEN |
| 10-11 | **Scale** — Bigger picture, 24/7, compounding value | GREEN |
| 12-13 | **Urgency** — Competitors are ahead, time is running out | RED/ACCENT |
| 14 | **CTA** — DM "[keyword]" to get started | GREEN + terminal |

## Step-by-Step Execution

### Step 1: Write the Script
Create a 15-scene table with:
- Scene text (2 lines max, separated by `\n`)
- Graphic concept for each scene
- SFX prompt for each scene

Present to user for approval before building (unless they say "just build it").

### Step 2: Create the Composition
**File**: `tiktok-recreation/src/{ComponentName}.tsx`

Follow the exact structure of `AIAutomation.tsx`:
```
- Imports (React, Remotion, Audio, TransitionSeries, fade, loadFont)
- Constants (W, H, CX, CY, SD=70, FADE=10, colors)
- SCENES array (15 strings)
- TextBlock component (fade in/out + translateY)
- G0 through G14 graphic components (SVG + CSS animations)
- GRAPHICS array
- Scene wrapper (narration + SFX audio + TextBlock + Graphic)
- Main export with TransitionSeries
```

**Audio paths in Scene wrapper**:
- Narration: `narration-{slug}/scene_XX.mp3`
- SFX: `sfx-{slug}/sfx_XX.mp3`

**SFX volume pattern** (proven, don't change):
```tsx
volume={(f) => {
  const fadeIn = Math.min(f / 5, 1);
  const fadeOut = f > SD - FADE ? Math.max(1 - (f - (SD - FADE)) / FADE, 0) : 1;
  return 0.4 * fadeIn * fadeOut;
}}
```

### Step 3: Register in Root.tsx
**File**: `tiktok-recreation/src/Root.tsx`

Add import and Composition entry:
```tsx
import { ComponentName } from "./ComponentName";

<Composition
  id="ComponentName"
  component={ComponentName}
  durationInFrames={1190}
  fps={30}
  width={1080}
  height={1920}
/>
```

### Step 4: Create & Run Narration Script
**File**: `execution/generate_{slug}_narration.py`

Pattern from `generate_automation_narration.py`:
- Voice: Roger (`CwhRBWXzGAHq8TQ4Fs17`)
- Model: `eleven_multilingual_v2`
- Voice settings: stability=0.6, similarity_boost=0.75, style=0.3
- Output: `tiktok-recreation/public/narration-{slug}/scene_00.mp3` ... `scene_14.mp3`
- Skip existing files (idempotent)
- 0.3s delay between calls

**Important**: Narration text should be speakable — spell out numbers ("four thousand" not "$4,000"), remove special characters, no emoji.

### Step 5: Create & Run SFX Script
**File**: `execution/generate_{slug}_sfx.py`

Pattern from `generate_automation_sfx.py`:
- Uses shared `execution/replicate_sfx.py` module — `from replicate_sfx import generate_sfx`
- Model: `sepal/audiogen` on Replicate (~$0.012/run, ~$0.18/video for 15 scenes)
- All durations: 2.5s (AudioGen accepts integer seconds, rounds down)
- Output: `tiktok-recreation/public/sfx-{slug}/sfx_00.mp3` ... `sfx_14.mp3`
- Skip existing files (idempotent)
- 1.0s delay between calls
- Requires `REPLICATE_API_TOKEN` in `.env`

**No ElevenLabs credits used for SFX.** ElevenLabs is reserved for TTS narration only.

### Step 6: Type-Check & Render
```bash
cd tiktok-recreation
npx tsc --noEmit
npx remotion render ComponentName out/{slug}.mp4
```

### Step 7: Open & Verify
```bash
open out/{slug}.mp4
```

Check:
- All 15 scenes have narration + SFX
- Transitions are clean
- Graphics match scene messaging
- CTA is clear

## Graphic Design Rules
- Use **SVG** for icons/shapes (clean at any scale)
- Use **CSS animations** via `interpolate()`, `spring()`, and `Math.sin()` for motion
- RED for problems/pain, GREEN for solutions/wins, ACCENT for urgency/highlights
- Each graphic should have **opacity fade-in** using spring or interpolate
- Scene 14 (CTA) always uses the **terminal typing pattern** with a relevant icon
- Reuse the **robot icon pattern** (antenna, head, eyes, mouth) for AI-related scenes
- Reuse the **racing robots pattern** (G12 from AIAutomation) for competitor scenes

## Naming Conventions
- Component: PascalCase (e.g., `EmailAutomation`, `VoiceReceptionist`, `WhyAds`)
- Slug: kebab-case (e.g., `email`, `receptionist`, `whyads`)
- Audio dirs: `narration-{slug}/`, `sfx-{slug}/`
- Output: `out/{slug}.mp4`
- Scripts: `execution/generate_{slug}_narration.py`, `execution/generate_{slug}_sfx.py`

**Important**: Check existing script filenames before creating new ones. If `generate_ads_narration.py` already exists for a different video, use a unique name like `generate_whyads_narration.py`.

## Files Produced Per Video

| Type | Path |
|------|------|
| Composition | `tiktok-recreation/src/{Component}.tsx` |
| Registration | `tiktok-recreation/src/Root.tsx` (modified) |
| Narration script | `execution/generate_{slug}_narration.py` |
| SFX script | `execution/generate_{slug}_sfx.py` |
| Narration audio | `tiktok-recreation/public/narration-{slug}/` (15 files) |
| SFX audio | `tiktok-recreation/public/sfx-{slug}/` (15 files) |
| Final video | `tiktok-recreation/out/{slug}.mp4` |

## Existing Videos (Reference)
- `AIAutomation.tsx` → AI automation ROI pitch (the original template)
- `EmailAutomation.tsx` → AI email automation
- `VoiceReceptionist.tsx` → AI after-hours voice receptionist
- `WhyAds.tsx` → Why ads are important for business
- `WhySEO.tsx` → Why SEO matters
- `WhyWebsite.tsx` → Why you need a website
- `GoodBadAds.tsx` → Good vs bad ad design

## Edge Cases
- **Replicate SFX failure**: If AudioGen returns an error, check `REPLICATE_API_TOKEN` in `.env` and account balance at replicate.com. Each SFX run costs ~$0.012.
- **Filename conflicts**: Always check `execution/` for existing scripts with similar names before creating new ones.
- **Long narration text**: Keep each scene's narration under ~8 words for punchiness. The voice reads at ~2 words/second, so 2.33s per scene = max ~5 words ideally.
- **TypeScript errors**: Run `npx tsc --noEmit` before rendering. Common issues: missing imports, unused variables, SVG attribute types.
