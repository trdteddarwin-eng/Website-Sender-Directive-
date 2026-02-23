# Speaker Notes & B-Roll Guide

**Video:** How I Built an AI Video Pipeline with Claude Code
**Total Runtime Target:** 18-20 minutes

---

## General Recording Notes

- Record screen captures BEFORE narrating. Have all the terminal sessions, VS Code windows, and finished videos queued up and ready.
- Use a 1080p screen recording for code shots. Zoom in to ~150% in VS Code so text is legible on YouTube.
- For the terminal, use a dark theme with at least 16pt font. Green-on-black terminal aesthetic matches the brand colors.
- Keep a clean desktop. Hide dock, menubar, notifications.
- For code walkthroughs, scroll slowly. Let each section breathe for 2-3 seconds before moving on.

---

## Section-by-Section Notes

### Hook (0:00 -- 0:30)

**Key talking points:**
- Sell the outcome immediately. Don't explain what it is -- show what it does.
- The split-screen before/after is the single most important shot of the video. Spend time getting this right.
- "12 videos shipped" is the credibility statement. Not a proof of concept -- a production system.

**B-Roll needed:**
- [ ] Screen recording: terminal with the one-line prompt, output scrolling
- [ ] Quick-cut montage of 5 finished videos (1 second each). Use: AIAutomation, WhyAds, SmartAI, EmailAutomation, SocialMediaMarketing
- [ ] Split-screen composition (can do this in CapCut or Premiere)

**Things to remember:**
- Keep energy high. This is the hook -- if you lose them here, they're gone.
- Don't oversell. "Five minutes" is accurate. Don't say "30 seconds" because the Remotion render alone takes 2-3 minutes.

---

### The Problem (0:30 -- 2:00)

**Key talking points:**
- The audience is builders and creators. They've felt this pain. Lean into it.
- The time breakdown (3 hours for a 40-second video) is the key stat. Make it feel absurd.
- The realization that every video has the same structure is the pivot moment. That's the "aha" -- if structure is constant, execution can be automated.

**B-Roll needed:**
- [ ] Screen recording: bouncing between apps (text editor, ElevenLabs dashboard, Remotion studio, file manager). Make it look chaotic.
- [ ] Timer graphic counting up (can be a simple animated overlay)
- [ ] Side-by-side of two finished videos showing the same structural pattern

**Things to remember:**
- Don't trash manual editing. Frame it as "great for one-offs, terrible at scale."
- The "mechanical vs creative" distinction is important. Emphasize that the creative decisions (topic, angle, messaging) are still human. Only the execution is automated.

---

### Architecture Overview (2:00 -- 4:00)

**Key talking points:**
- The three-layer diagram is the thesis of the video. Spend time on it.
- The probability math (90% per step = 59% over 5 steps) is the most shareable moment. People will screenshot this.
- Make the layers concrete. Directive = markdown file. Orchestration = Claude Code. Execution = Python script. No abstraction.

**B-Roll needed:**
- [ ] Architecture diagram (create in Figma or Excalidraw). Three horizontal bands: blue "Directives" at top, purple "Orchestration" in middle, green "Execution" at bottom. Arrows flowing down.
- [ ] Quick shot of the `directives/` folder in VS Code
- [ ] Quick shot of Claude Code terminal
- [ ] Quick shot of the `execution/` folder in VS Code
- [ ] "Probability" slide: `90%^5 = 59%` on left, `AI + Scripts = 99%` on right

**Things to remember:**
- This section is conceptual. Keep it visual. Don't read code here -- save that for later sections.
- The probability argument is the intellectual hook for engineers. Deliver it clearly.
- Mention that this pattern works for ANY repeatable workflow, not just video.

---

### Layer 1: Directives (4:00 -- 6:00)

**Key talking points:**
- The directive is a markdown file, not code. That's intentional -- anyone can read and update it.
- Walk through the Scene Script Formula table slowly. It's the most interesting artifact.
- The color-coding (RED = problems, GREEN = solutions) maps directly to the video's visual design. The directive defines the creative language.
- The file output table at the end shows how one directive produces 7+ artifacts per video.

**B-Roll needed:**
- [ ] Full-screen VS Code showing `directives/tiktok_video.md`, scrolling from top to bottom at reading speed
- [ ] Zoom-in shots of each key section: Trigger, Architecture, Scene Script Formula, Step-by-Step Execution, Files Produced
- [ ] Side-by-side of the formula table and a finished video playing, with highlights showing which scenes map to which row
- [ ] Quick shot of the brand color swatches: #FF3B3B, #4ADE80, #FBBF24, #60A5FA

**Things to remember:**
- Read key phrases from the directive on screen. "15 scenes, 70 frames each." "TransitionSeries with 10-frame fade transitions." This grounds the abstraction.
- Mention the "Existing Videos" section at the bottom. It lists 7 reference compositions. This is how the agent knows the standard.
- Don't skip the naming conventions section. Slug format (kebab-case) vs component format (PascalCase) matters when you have 12 videos.

---

### Layer 2: Orchestration (6:00 -- 8:00)

**Key talking points:**
- The orchestration layer is where the AI earns its keep. It's not running scripts blindly -- it's making decisions.
- Three key decision types: (1) Sequencing -- which step to run next. (2) Idempotency -- skip work that's already done. (3) Error recovery -- fix and retry.
- The narration text requires judgment calls. "Twenty four seven" not "24/7." "Ten times" not "10x." The agent handles these transformations.
- Script approval is a human-in-the-loop checkpoint. The agent proposes, the human approves.

**B-Roll needed:**
- [ ] Screen recording: Claude Code processing a video request from start to finish (speed this up 4x for the montage)
- [ ] Close-up of Claude reading the directive and listing the steps
- [ ] Close-up of Claude checking for existing files: "Scene 00 already exists, skipping"
- [ ] Close-up of Claude hitting a TypeScript error, reading it, and fixing the code
- [ ] Terminal showing the script approval prompt and user typing "looks good"

**Things to remember:**
- This is the hardest section to make visual. The agent's "thinking" happens in text. Use zoom-ins on key terminal lines to make it engaging.
- Don't spend too long on this. The audience wants to see code and output, not agent logs. Keep it brisk.
- Emphasize: the agent doesn't know HTTP, doesn't know ElevenLabs API details, doesn't know Remotion rendering. It just calls scripts. That's the power of the layer separation.

---

### Layer 3: Execution (8:00 -- 11:00)

**Key talking points:**
- This is the code walkthrough section. Slow down and show actual code.
- The narration script: voice ID CwhRBWXzGAHq8TQ4Fs17 (Roger), model eleven_multilingual_v2, voice settings stability=0.6 / similarity_boost=0.75 / style=0.3.
- Idempotency: `if os.path.exists` check before every API call. Re-run safe.
- Rate limit protection: 0.3s delay for TTS, 1.0s delay for SFX.
- The SFX prompts are descriptive natural language. "Dramatic tension hit with low rumble, bar chart dropping, failure sound, dark and ominous." The quality of these prompts directly affects the output.
- Render command: `npx remotion render SmartAI out/smartai.mp4`

**B-Roll needed:**
- [ ] VS Code showing `generate_smartai_narration.py` -- full file, scrolling slowly
- [ ] VS Code showing `generate_smartai_sfx.py` -- full file, scrolling slowly
- [ ] Terminal running the narration script with output: "Scene 00: 14.2KB... Scene 01: 12.8KB..."
- [ ] Finder window showing `narration-smartai/` with 15 MP3 files
- [ ] Finder window showing `sfx-smartai/` with 15 MP3 files
- [ ] Terminal running `npx tsc --noEmit` (pass) then `npx remotion render SmartAI out/smartai.mp4` with frame progress
- [ ] Play the finished smartai.mp4 for 5 seconds

**Things to remember:**
- Show the actual API response sizes (KB per file). It makes it feel real.
- Mention that each narration script is unique per video -- `generate_smartai_narration.py` vs `generate_ads_narration.py` vs `generate_email_narration.py`. The agent creates a new one for each video, populated with the right scene text.
- Don't skip the SFX prompts. They're the most creative part of the execution layer. Read 2-3 aloud.

---

### Remotion Deep Dive (11:00 -- 13:00)

**Key talking points:**
- Remotion is React for video. Every animation is a function of the current frame number. No CSS animations.
- The composition structure: imports -> constants -> SCENES array -> TextBlock -> G0-G14 graphics -> Scene wrapper -> main export with TransitionSeries.
- TextBlock: opacity interpolation from frame 0->12 (fade in) and SD-10->SD (fade out). translateY from 24->0 with Easing.out(Easing.sin).
- Each graphic component (G0-G14) is standalone. Show 2-3 in detail: G0 (shrinking bars), G10 (3->30 multiplier with sparkles), G14 (terminal + rocket).
- The SFX volume curve: `0.4 * fadeIn * fadeOut` caps SFX at 40% volume so narration stays clear.
- Math: 15 sequences x (SD + FADE) frames - 14 overlaps x FADE = 1190 frames.

**B-Roll needed:**
- [ ] VS Code showing SmartAI.tsx with the file minimap visible on the right (shows the scale of the file)
- [ ] Zoom into the import block
- [ ] Zoom into the constants block (W, H, CX, CY, SD, FADE, colors)
- [ ] Zoom into the TextBlock component
- [ ] Quick montage: play each of the 15 scenes for ~1 second each, showing the graphic for that scene
- [ ] Zoom into G0 (shrinking bars) code, then show the rendered G0 scene
- [ ] Zoom into G14 (terminal + rocket) code, then show the rendered G14 scene
- [ ] Zoom into the Scene wrapper and the SFX volume function
- [ ] Zoom into the TransitionSeries in the main export

**Things to remember:**
- This is the section most likely to lose non-technical viewers. Keep it moving. Show code, then immediately show the rendered result. Code -> output. Code -> output.
- The `spring()` vs `interpolate()` distinction matters. Spring for entrances (smooth or bouncy depending on damping). Interpolate for timed linear animations. Show examples of both.
- Mention the hard rule: NO CSS animations. Remotion needs frame-precise control. This is a common Remotion beginner mistake.

---

### CapCut Integration (13:00 -- 16:00)

**Key talking points:**
- CapCut stores projects as `draft_info.json` plus media in `Resources/`.
- The reverse-engineering story is compelling. Mention creating manual projects, exporting JSON, diffing to understand the format.
- The placeholder paths bug: first version used relative paths, CapCut requires absolute paths to Resources/ folder. This was the key breakthrough.
- Three outputs: draft_info.json (project structure), media files copied to Resources/, root_meta_info.json updated.
- End result: open CapCut on iPad, project is there, fully loaded, all tracks aligned.

**B-Roll needed:**
- [ ] Finder showing the CapCut project folder structure
- [ ] VS Code showing the draft_info.json structure (zoom into materials, tracks, segments)
- [ ] Side-by-side diff of two draft_info.json files (manual vs generated)
- [ ] Finder showing Resources/ folder with all 31 files
- [ ] Screen recording on iPad: open CapCut, find the project, tap into it, scroll through the timeline
- [ ] Close-up of the CapCut timeline showing video track, narration track, SFX track all aligned

**Things to remember:**
- If CapCut script doesn't exist yet in the repo, this section is about the concept and the reverse engineering journey. Frame it as "here's what I built and how" rather than "here's the exact code."
- The iPad angle matters. A lot of creators edit on iPad. Generating a project that syncs via iCloud to CapCut on iPad is a genuine workflow win.
- Don't get lost in JSON details. Show the structure at a high level, then jump to the result.

---

### Live Demo (16:00 -- 18:00)

**Key talking points:**
- This is the payoff. Everything the viewer has been watching builds to this moment.
- Keep it simple. One prompt. Watch it run. Show the output.
- Call out the timing. Total time from prompt to playback: ~4.5 minutes. Three of those minutes are the Remotion render.
- Show the `out/` directory with all 12 videos at the end. That's the proof of scale.

**B-Roll needed:**
- [ ] Clean terminal, dark theme, cursor blinking
- [ ] Type the prompt live (or use a pre-recorded session sped up). Real terminal output, not fake.
- [ ] Claude reading the directive (show for 2-3 seconds)
- [ ] Script generation (show the 15-scene table appearing)
- [ ] Narration generation (terminal output scrolling)
- [ ] SFX generation (terminal output scrolling)
- [ ] TypeScript check (show "pass")
- [ ] Remotion render progress bar
- [ ] Play the finished video full screen for 10-15 seconds
- [ ] Finder showing `out/` directory with all 12 MP4 files

**Things to remember:**
- If possible, record a real pipeline run for this section. If it's too risky (API errors, credits, etc.), use a pre-recorded run with real output. DO NOT fake it.
- Speed up the boring parts (narration download, SFX download) at 4x. Show the render at 2x. Play the final video at 1x.
- The "12 videos shipped" moment should feel like a mic drop. Show the full directory listing.

---

### Self-Annealing (18:00 -- 19:00)

**Key talking points:**
- Self-annealing = the system learns from its own mistakes.
- The error log format: what happened, why, fix, rule.
- Highlight 2-3 real entries. The MediaPipe version pin and the designer timeout are the most relatable.
- The flywheel: errors -> fixes -> documented rules -> agent reads rules -> fewer errors -> more reliable system.
- The agent scans the error log before every task. Past mistakes become permanent institutional knowledge.

**B-Roll needed:**
- [ ] VS Code showing the Error Log section of CLAUDE.md, scrolling through entries
- [ ] Zoom into the MediaPipe entry
- [ ] Zoom into the Designer timeout entry
- [ ] Zoom into the CapCut placeholder paths entry (if it exists)
- [ ] Diagram: circular arrow with "Error -> Fix -> Log -> Read -> Prevent" steps

**Things to remember:**
- This is the intellectual capstone. The three-layer architecture is the "how." Self-annealing is the "why it keeps working."
- Don't spend too long on individual entries. Two examples, clearly explained, is enough.
- End this section with energy. "It never makes the same mistake twice." That's the line.

---

### Outro + CTA (19:00 -- 20:00)

**Key talking points:**
- Recap the three layers in one sentence each.
- Broaden beyond video: this pattern works for any repeatable process with creative decisions up front.
- Mention the GitHub link (put actual URL in description).
- CTA: subscribe for more AI automation content.

**B-Roll needed:**
- [ ] Architecture diagram one more time (callback to the overview section)
- [ ] Grid of all 12 video thumbnails (create this in Figma or use Remotion)
- [ ] Text slide: "Creative decisions = Human. Mechanical execution = Automated. Routing between them = AI."
- [ ] GitHub repo page (if public)
- [ ] End card with subscribe button and "next video" suggestion

**Things to remember:**
- Keep the outro tight. Don't ramble. State the takeaway, give the CTA, end.
- "Go build something" is the final line. Deliver it with conviction and cut to black.

---

## Post-Production Checklist

- [ ] Background music: subtle lo-fi or ambient electronic, ducked under narration. No lyrics.
- [ ] Chapters: add YouTube chapters matching the section timestamps.
- [ ] Description: include timestamps, GitHub link, links to tools mentioned (ElevenLabs, Remotion, CapCut, Claude Code).
- [ ] Thumbnail: terminal screenshot with text overlay "AI Video Pipeline" and a before/after arrow.
- [ ] Tags: Claude Code, AI automation, Remotion, TikTok automation, AI video generation, ElevenLabs, CapCut, developer tools.
- [ ] End screen: link to related video (if exists) + subscribe button.

---

## Key Numbers to Get Right

| Fact | Value |
|------|-------|
| Scenes per video | 15 |
| Frames per scene (SD) | 70 |
| Fade overlap (FADE) | 10 |
| Total frames | 1,190 |
| FPS | 30 |
| Total duration | ~39.7 seconds |
| Resolution | 1080 x 1920 |
| Voice | Roger (CwhRBWXzGAHq8TQ4Fs17) |
| TTS model | eleven_multilingual_v2 |
| SFX model | eleven_text_to_sound_v2 |
| SFX clip duration | 2.5 seconds |
| SFX volume cap | 0.4 (40%) |
| Videos shipped | 12 |
| TTS rate limit delay | 0.3s |
| SFX rate limit delay | 1.0s |
| Brand RED | #FF3B3B |
| Brand GREEN | #4ADE80 |
| Brand ACCENT | #FBBF24 |
| Brand BLUE | #60A5FA |
| Render time (approx) | 2-3 minutes |
| Total pipeline time | ~4.5 minutes |
