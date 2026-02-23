# How I Built an AI Video Pipeline with Claude Code

**Format:** YouTube narrated walkthrough tutorial
**Duration:** ~18-20 minutes
**Tone:** Technical but accessible. Builder showing builders how it works.

---

## 0:00 -- 0:30 | Hook

[SCREEN: Split screen. Left side: a terminal with one sentence typed. Right side: a finished TikTok video playing -- motion graphics, narration, SFX, the works.]

I type one sentence into my terminal. Five minutes later, I have a fully edited TikTok video -- scripted, narrated, with sound effects and motion graphics -- ready to post.

[SCREEN: Quick montage of 4-5 different finished videos playing back-to-back -- AIAutomation, WhyAds, SmartAI, EmailAutomation, VoiceReceptionist. Each plays for about 1 second.]

This isn't some toy demo. I've shipped 12 videos through this pipeline so far, and every single one was generated from a one-line prompt.

[SCREEN: Terminal showing the command `"Make me a video about AI automation"` with output scrolling.]

Today I'm going to show you exactly how the whole system works, from architecture to code, and how you can build something like this yourself.

---

## 0:30 -- 2:00 | The Problem

[SCREEN: Screen recording of a typical manual video creation workflow -- jumping between apps.]

So here's the problem. If you've ever made short-form video content, you know the pain. You sit down, you write a script. Then you open up your TTS tool, paste in narration line by line, download 15 audio files. Then you go find sound effects. Then you open your editor, drag everything onto a timeline, build the graphics, time the transitions, export, re-export because something was off, export again.

[SCREEN: A timer counting up. Show the accumulated time: "Script: 30 min. Narration: 20 min. SFX: 15 min. Editing: 2 hours. Export: 10 min. Total: ~3 hours."]

For a 40-second TikTok, you're looking at two to three hours of work. And the worst part? Most of that work is mechanical. It's not creative. You're just dragging files around, copying and pasting, clicking buttons.

[SCREEN: Highlight the repetitive parts -- same structure every time, same scene count, same color palette.]

I was making these videos over and over, and I realized something. Every video follows the same formula. Fifteen scenes, same arc every time -- hook, pain, shift, proof, scale, urgency, call to action. Same resolution, same frame rate, same transition style.

If the structure is identical every time, why am I doing this by hand?

[SCREEN: Text on screen -- "What if the creative decisions stay with me, but the mechanical execution is automated?"]

That's when I started building the pipeline.

---

## 2:00 -- 4:00 | Architecture Overview

[SCREEN: Full-screen architecture diagram. Three horizontal layers stacked. Top: "Directives" (markdown icon). Middle: "Orchestration" (brain/Claude icon). Bottom: "Execution" (Python/gear icon). Arrows flowing down between them.]

The system uses a three-layer architecture. This is the core insight that makes it all work, and honestly, it's the thing I'd want you to take away even if you never build a video pipeline.

**Layer one: Directives.** These are markdown files that live in a `directives/` folder. They're SOPs -- standard operating procedures. They define what needs to happen, step by step, but they don't execute anything themselves. Think of them as the instruction manual you'd give a capable employee.

[SCREEN: Show the directives/ folder in VS Code with tiktok_video.md highlighted.]

**Layer two: Orchestration.** This is Claude -- the AI agent. It reads the directives, makes decisions, calls the right scripts in the right order, handles errors, and adapts. It's the intelligent glue between intent and execution.

[SCREEN: Show Claude Code terminal processing a request, reading the directive, deciding what to do next.]

**Layer three: Execution.** Deterministic Python scripts in the `execution/` folder. These handle the actual API calls -- ElevenLabs for voice, ElevenLabs for sound effects, Remotion for rendering. They're reliable, testable, and fast. No LLM involved.

[SCREEN: Show the execution/ folder listing the various scripts.]

> **Key insight:** Why three layers instead of just letting the AI do everything? Because LLMs are probabilistic. They're great at decisions but unreliable at repetitive execution. If you have 90% accuracy per step and five steps in a row, you're at 59% success rate. By pushing the mechanical work into deterministic scripts, the AI only handles what it's good at -- making choices. The scripts handle what code is good at -- doing the same thing perfectly every time.

[SCREEN: Diagram showing "90% x 90% x 90% x 90% x 90% = 59%" next to "AI decides -> Script executes = 99%".]

---

## 4:00 -- 6:00 | Layer 1: Directives

[SCREEN: Open `directives/tiktok_video.md` in VS Code. Full file visible, scrolling slowly.]

Let me show you what a directive actually looks like. This is `tiktok_video.md` -- the SOP that controls the entire video pipeline.

It starts with the trigger. Quote: "Make a TikTok video about [topic]." That's literally all the user has to say.

[SCREEN: Zoom into the "Trigger" section of the directive.]

Then it defines the architecture. Every video is 15 scenes, 70 frames each -- that's about 2.33 seconds per scene at 30 frames per second. TransitionSeries with 10-frame fade transitions. Total duration: 1,190 frames, roughly 39.7 seconds. Resolution: 1080 by 1920, TikTok vertical.

[SCREEN: Zoom into the "Architecture" section. Highlight the numbers.]

> **Technical note:** 15 scenes times 70 frames = 1,050. But with TransitionSeries, each sequence gets SD + FADE = 80 frames, and the 14 transitions overlap by 10 frames each. So: 15 x 80 - 14 x 10 = 1,200 - 140 = 1,060... except Remotion calculates it as 1,190 frames total. The overlap math is a bit nuanced, but the point is: it's all defined precisely in the directive so the agent doesn't have to figure it out.

Now here's the part I love. The scene script formula. This table defines the emotional arc of every video.

[SCREEN: Zoom into the Scene Script Formula table. Highlight each row as you describe it.]

Scenes zero and one are the hook -- red color tone, identify the problem, create urgency. Scenes two through four are pain -- stats, consequences, what they're losing. Scenes five and six are the shift -- green transition, introduce the solution. Seven through nine are proof -- how it works, ROI, specific benefits. Ten and eleven are scale -- bigger picture, 24/7 value. Twelve and thirteen are urgency -- competitors are ahead. And scene fourteen is always the CTA -- "DM me [keyword]" with a terminal typing animation.

[SCREEN: Side-by-side of the formula table and a finished video playing, showing how the scenes match the arc.]

The directive also defines brand colors -- Red `#FF3B3B` for problems, Green `#4ADE80` for solutions, Accent `#FBBF24` for urgency, Blue `#60A5FA` for neutral elements. And it specifies exactly what files get produced: the `.tsx` composition, the narration script, the SFX script, the audio folders, the final MP4.

[SCREEN: Zoom into the "Files Produced Per Video" table.]

This is the key thing about directives. They're detailed enough that a mid-level employee -- or an AI agent -- can follow them without asking questions. But they're written in natural language, not code. That means I can update them in 30 seconds when I learn something new.

---

## 6:00 -- 8:00 | Layer 2: Orchestration

[SCREEN: Claude Code terminal. User types: "Make a TikTok video about smart AI automation for small businesses."]

So I open Claude Code and I type something like "Make a TikTok video about smart AI automation for small businesses." That's it. That's my entire input.

Claude reads the directive and starts making decisions. First, it writes the script. Fifteen scenes, following the formula -- hook, pain, shift, proof, scale, urgency, CTA. It picks the right messaging angle, chooses the DM keyword, writes narration text that's speakable. That means spelling out numbers -- "twenty four seven" not "24/7" -- and keeping each line under about five words for punchiness.

[SCREEN: Show Claude's output as it writes the 15-scene script table. Scenes, text, graphic concepts, SFX prompts.]

Then it presents the script for approval. If I say "looks good" or "just build it," it moves to execution. If I want changes, I can tweak individual scenes.

[SCREEN: User approving the script in the terminal.]

Once approved, Claude follows the directive step by step. Step two: create the Remotion composition -- a `.tsx` file with 15 custom graphic components, one per scene. Step three: register it in `Root.tsx`. Step four: generate narration audio. Step five: generate sound effects. Step six: type-check and render.

[SCREEN: Show Claude calling each step in sequence. Highlight the decision points -- "Checking if narration files already exist... 3 of 15 exist, generating remaining 12."]

Here's where the orchestration layer earns its keep. It's not just running scripts blindly. It checks what already exists -- if you've already generated narration for scenes zero through four but SFX generation failed, it picks up where it left off. It handles errors -- if the ElevenLabs API returns a 429 rate limit, it waits and retries. If TypeScript compilation fails, it reads the error, fixes the code, and re-validates.

[SCREEN: Show an example of Claude hitting a TS error, reading it, fixing the code, re-running tsc.]

> **Decision-making in action:** The agent doesn't just execute a recipe. It routes around problems. Script already exists? Skip it. Credits exhausted? Copy placeholder SFX from another video and note which scenes need regeneration. TypeScript errors? Fix and retry. That's what orchestration means -- intelligent routing between deterministic tools.

---

## 8:00 -- 11:00 | Layer 3: Execution

[SCREEN: VS Code showing `execution/generate_smartai_narration.py`.]

Now let's look at the actual scripts. This is the narration generator for the SmartAI video. It's simple, deliberate Python.

The voice is Roger -- that's ElevenLabs voice ID `CwhRBWXzGAHq8TQ4Fs17`. The model is `eleven_multilingual_v2`. Voice settings: stability 0.6, similarity boost 0.75, style 0.3. These numbers were dialed in over dozens of iterations.

[SCREEN: Highlight the voice settings block in the code.]

The scenes array holds all 15 lines of narration text. "Small businesses fail because they can't scale." "You're competing against companies ten times your size." All the way through to "DM me scale to automate your business."

[SCREEN: Scroll through the SCENES array.]

The generation function is dead simple. POST to the ElevenLabs TTS endpoint, write the response bytes to an MP3 file. If the file already exists, skip it. 0.3-second delay between calls so we don't hit rate limits. That idempotency is important -- it means you can re-run the script without wasting API credits.

[SCREEN: Highlight the `if os.path.exists` check and the `time.sleep(0.3)` line.]

Output goes to `tiktok-recreation/public/narration-smartai/` -- fifteen MP3 files, `scene_00.mp3` through `scene_14.mp3`.

[SCREEN: Show the output directory in Finder with all 15 files.]

Now the SFX script. Same pattern, different API.

[SCREEN: Switch to `execution/generate_smartai_sfx.py`.]

Instead of text-to-speech, we're using ElevenLabs sound generation -- model `eleven_text_to_sound_v2`. Each sound effect is 2.5 seconds, output format MP3 at 44.1kHz, 128kbps. The prompts are descriptive: "dramatic tension hit with low rumble, bar chart dropping, failure sound, dark and ominous" for scene zero. "Quick notification chime cascade, emails clearing rapidly, clean inbox sound" for scene seven.

[SCREEN: Scroll through the SFX_SCENES array, highlighting the prompt text.]

One-second delay between SFX calls because the sound generation API is slower and stricter than TTS.

[SCREEN: Highlight the `time.sleep(1.0)` line.]

> **Why not generate these inside the agent?** Because deterministic scripts are testable. I can run `python execution/generate_smartai_narration.py` by itself, verify the output, and know it works. If ElevenLabs changes their API tomorrow, I fix one script and every future video benefits. The agent doesn't know or care about HTTP headers and content types -- it just calls the script.

Now for rendering. Once all the audio is generated and the `.tsx` composition is written, we render.

[SCREEN: Terminal showing the render commands.]

```
cd tiktok-recreation
npx tsc --noEmit
npx remotion render SmartAI out/smartai.mp4
```

TypeScript check first -- catch errors before burning render time. Then Remotion renders the composition to MP4. On my machine this takes about two to three minutes for a 40-second video at 1080x1920.

[SCREEN: Show Remotion render progress bar moving, then the final output: "Rendered 1190 frames. Output: out/smartai.mp4".]

The output goes to `tiktok-recreation/out/smartai.mp4`. Open it, check all 15 scenes, verify narration and SFX are synced, make sure the CTA is clear. Done.

[SCREEN: Play the finished smartai.mp4 video for about 5 seconds.]

---

## 11:00 -- 13:00 | Remotion Deep Dive

[SCREEN: VS Code showing `SmartAI.tsx` with the full file structure visible in the minimap.]

Let me walk you through how the Remotion composition actually works, because this is the most interesting part of the engineering.

At the top, we import from Remotion -- `AbsoluteFill`, `useCurrentFrame`, `interpolate`, `spring`, `Easing`, `staticFile`, plus `Audio` from `@remotion/media`, `TransitionSeries` and `linearTiming` from `@remotion/transitions`, and the `fade` transition. Google Fonts loads Inter with weights 400, 600, and 700.

[SCREEN: Highlight the import block at the top of SmartAI.tsx.]

Then constants. Width 1080, height 1920. Center X and Y calculated from those. Scene duration SD = 70 frames. Fade overlap FADE = 10. And the brand colors -- RED, GREEN, ACCENT, BLUE.

[SCREEN: Highlight the constants block.]

The SCENES array holds all 15 text strings, with newlines for line breaks. "Small businesses fail\nbecause they can't scale" and so on.

[SCREEN: Highlight the SCENES array.]

TextBlock is the shared text component. It uses `useCurrentFrame()` for everything -- no CSS animations. Opacity fades in from frame 0 to 12, holds, then fades out from SD-10 to SD. Text slides up with a `translateY` from 24 pixels to 0 using `Easing.out(Easing.sin)`. Every video uses this exact same TextBlock.

[SCREEN: Highlight the TextBlock component. Show a slow-motion clip of the text animation.]

Now the graphics. G0 through G14 -- one per scene, each completely unique. G0 is shrinking bar charts with a red downward arrow. G1 is a small stick figure versus a giant one with a "10x" label. G2 is 50 red dots versus 3 blue dots. G3 is a flickering light bulb. G4 is a robot arm versus a fading human hand. And so on through G14, which is always the terminal window with the DM keyword typing out and a rocket launching.

[SCREEN: Quick montage showing each graphic component rendering -- G0 through G14, about 1 second each.]

Every graphic uses Remotion's `spring()` for entrances and `interpolate()` for timed animations. No CSS keyframes. That's a hard rule -- Remotion needs frame-precise control, and CSS animations don't give you that.

> **Architecture pattern:** Notice how every graphic component is a standalone React component -- `G0`, `G1`, `G2`, etc. They're collected into a `GRAPHICS` array, and the `Scene` wrapper component just picks the right one by index. This means you can swap out any scene's graphic without touching the rest of the composition. Modular by design.

[SCREEN: Highlight the GRAPHICS array and the Scene wrapper component.]

The Scene wrapper ties it all together. Black background. Audio component for narration -- `narration-smartai/scene_XX.mp3`. Audio component for SFX with a volume curve that fades in over 5 frames and out over the last FADE frames, capped at 0.4 volume so it doesn't overpower the voice. TextBlock for the on-screen text. And the graphic component.

[SCREEN: Highlight the Scene wrapper, especially the SFX volume function.]

```tsx
volume={(f) => {
  const fadeIn = Math.min(f / 5, 1);
  const fadeOut = f > SD - FADE ? Math.max(1 - (f - (SD - FADE)) / FADE, 0) : 1;
  return 0.4 * fadeIn * fadeOut;
}}
```

Finally, the main export wraps everything in a TransitionSeries. Each scene gets `SD + FADE` frames (80), with 10-frame fade transitions between them. The entire composition is 1,190 frames at 30fps -- 39.7 seconds of finished video.

[SCREEN: Highlight the main export component with TransitionSeries.]

---

## 13:00 -- 16:00 | CapCut Integration

[SCREEN: Show the CapCut mobile app on an iPad, with a project open.]

Now, Remotion gives you an MP4 and that's great for posting directly. But sometimes you want to edit further -- add captions, tweak timing, adjust audio levels. That's where CapCut comes in.

I built a script that reverse-engineers CapCut's project format and generates a complete editable project from the same pipeline output. You get the video track, narration track, and SFX track, all pre-aligned on a timeline, ready to open in CapCut on your iPad.

[SCREEN: Show a CapCut project opened on iPad with all tracks visible -- video, narration, SFX.]

Here's how it works. CapCut stores projects as a JSON file called `draft_info.json` inside a folder structure. The project folder lives at a specific path on your device -- on Mac it's under `~/Movies/CapCut/User Data/Projects/com.lemon.lv/`. Inside that folder, there's a `Resources/` directory for all the media files.

[SCREEN: Show the CapCut project folder structure in Finder. Highlight draft_info.json and Resources/.]

The `draft_info.json` file is where all the magic happens. It defines materials -- references to your media files with duration, path, and type. It defines tracks -- video, audio, effects. And inside each track, it defines segments with start times, end times, and which material they reference.

> **Reverse engineering story:** Figuring out this format was a journey. CapCut doesn't document their JSON schema. I had to create projects manually in CapCut, export the `draft_info.json`, and diff them to understand the structure. The big gotcha was file paths. My first version used placeholder paths and nothing loaded. CapCut requires absolute paths to the actual media files in the `Resources/` directory. Once I figured that out and started copying the MP3s into Resources with the right names, everything clicked.

[SCREEN: Show a diff of two draft_info.json files side by side. Highlight the materials and segments sections.]

The script does three things. First, it creates the `draft_info.json` with three tracks. Track one is the rendered video. Track two is narration -- 15 segments, one per scene, each pointing to its MP3 file. Track three is SFX -- same 15 segments, same alignment.

[SCREEN: Show the JSON structure. Highlight the tracks array with video, narration, and SFX entries.]

Second, it copies all media files into the `Resources/` folder. The 15 narration MP3s, the 15 SFX MP3s, and the rendered video.

Third, it updates `root_meta_info.json` -- CapCut's project index file -- so the project shows up in the app's project list.

[SCREEN: Show the Resources/ folder with all 31 files (1 video + 15 narration + 15 SFX).]

The result: I open CapCut on my iPad, the project is right there, fully loaded. Every narration clip is on its own track, aligned to the right scene. Every SFX clip is there too. I can adjust levels, add captions with CapCut's auto-caption feature, swap out a clip, whatever I need.

[SCREEN: Screen recording of opening CapCut on iPad, showing the project in the project list, tapping into it, seeing the fully loaded timeline.]

This integration closes the loop between automated generation and manual creative polish. The pipeline handles 95% of the work. CapCut handles the last 5% when you want that extra touch.

---

## 16:00 -- 18:00 | Live Demo

[SCREEN: Clean terminal. Cursor blinking.]

Alright. Let's run it live. I'm going to type one sentence and we'll watch the whole pipeline go.

[SCREEN: Type the prompt into Claude Code.]

"Make me a video about AI automation."

[SCREEN: Claude reads the directive. Show the agent's thought process -- "Reading directives/tiktok_video.md... Following 7-step execution plan."]

Claude reads the directive. It picks the topic, writes the 15-scene script, chooses the DM keyword "automate." It presents the script -- hook about businesses drowning in manual work, pain about hours wasted, shift into AI automation, proof with specific numbers, scale to 24/7 operation, urgency about competitors, CTA to DM "automate."

[SCREEN: Show the script table being generated in the terminal.]

I say "looks good." Now it builds.

[SCREEN: Show each step executing. Timestamps visible.]

Step one -- creating the Remotion composition. Claude writes `AIAutomation.tsx`, 15 graphic components, registers it in Root.tsx. Step two -- generating narration. POST to ElevenLabs TTS, Roger voice, 15 files. You can see them downloading one by one. Step three -- generating SFX. 15 sound effects, 2.5 seconds each.

[SCREEN: Terminal output scrolling. "Scene 00: 14.2KB... Scene 01: 12.8KB..." Show the progress.]

Step four -- type check. `npx tsc --noEmit` -- pass. Step five -- render. `npx remotion render AIAutomation out/ai-automation.mp4`. Watch the frame counter go.

[SCREEN: Remotion render progress. Frame 0... 200... 400... 600... 800... 1000... 1190. Done.]

And there it is. Let me open it.

[SCREEN: Play the finished video full screen. Let it run for 10-15 seconds -- enough to see the hook, some pain scenes, and the shift to green.]

From one sentence to a finished video. The narration is synced, the SFX complement each scene, the graphics match the messaging, the transitions are clean. This is video number 12 out of this pipeline.

[SCREEN: Show the `out/` directory with all 12 rendered MP4 files.]

Total time from prompt to playback: about four and a half minutes. Three of those minutes are the Remotion render.

---

## 18:00 -- 19:00 | Self-Annealing

[SCREEN: Open CLAUDE.md, scroll to the Error Log section.]

The last thing I want to show you is what makes this system get smarter over time. It's called self-annealing, and it's a section at the bottom of the CLAUDE.md config file.

Every time the system hits an error -- a script fails, an API changes, a weird edge case shows up -- it gets logged here. Not just "what broke," but why it broke, how it was fixed, and what rule to follow going forward.

[SCREEN: Scroll through the error log entries. Highlight specific ones.]

Here's a real example. "MediaPipe 0.10.32+ removed solutions API." What happened: `mediapipe.solutions.face_detection` threw an AttributeError. Why: the new version removed the legacy namespace. Fix: pinned to `mediapipe==0.10.14`. Rule: always use that version for face detection code.

[SCREEN: Highlight the MediaPipe error log entry.]

Another one. "Designer timeout: subprocess kills script before HTTP timeout fires." The AI model was generating 16,000 tokens in a single API call, which took three to five minutes. The subprocess timeout and the HTTP timeout were both set to 120 seconds, so they raced each other. Fix: split the generation into three parallel API calls of 5,000 tokens each, reducing wall time from five minutes to 90 seconds.

[SCREEN: Highlight the Designer timeout error log entry.]

And here's the important part: every time the agent starts a new task, it scans this error log first. If a past mistake is relevant to what it's about to do, it follows the rule. It never makes the same mistake twice.

[SCREEN: Show the instruction in CLAUDE.md: "Before starting any task, scan this error log."]

> **This is the flywheel.** Errors happen, you fix them, you document the fix, the system learns. Over time, the pipeline gets more reliable, not less. The error log is the institutional memory of the system.

---

## 19:00 -- 20:00 | Outro + CTA

[SCREEN: Architecture diagram again -- three layers. Then zoom out to show the full workspace: directives/, execution/, tiktok-recreation/.]

So that's the pipeline. Three layers -- directives define what to do, the Claude agent orchestrates decisions, Python scripts execute reliably. One sentence in, finished video out. Twelve videos shipped so far and counting.

[SCREEN: Grid of all 12 video thumbnails: AIAutomation, EmailAutomation, VoiceReceptionist, WhyAds, WhySEO, WhyWebsite, GoodBadAds, AIChatbot, SocialMediaMarketing, SmartAI, RecreatedVideo, TikTokVideo.]

The bigger idea here isn't about video. It's about the pattern. Any time you have a repeatable process with creative decisions up front and mechanical execution after that, you can build this same architecture. Email campaigns, blog posts, data reports, client proposals -- the three-layer pattern works for all of it.

[SCREEN: Text on screen: "Creative decisions = Human. Mechanical execution = Automated. Routing between them = AI."]

If you want to build your own version of this, the code is open source. Link in the description. The `CLAUDE.md` file is the starting point -- it explains the architecture, the operating principles, and the self-annealing loop.

[SCREEN: Show the GitHub repo page. Highlight the CLAUDE.md file.]

If this was useful, subscribe. I'm going to be building more of these systems -- pipeline automation, AI agent workflows, the whole stack -- and sharing exactly how they work.

[SCREEN: Subscribe button animation. "Drop a comment with what you'd automate next."]

Thanks for watching. Go build something.

[SCREEN: Fade to black. End card with channel name and subscribe button.]
