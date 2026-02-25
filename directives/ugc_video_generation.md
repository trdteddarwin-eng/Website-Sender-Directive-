# UGC Video Generation Pipeline

## Overview
Generate multi-scene UGC (User Generated Content) ads from a single avatar image + product image. Designed for TikTok Shop, Reels, and Meta ads.

## Architecture
- **Script:** `execution/generate_ugc_video.py`
- **Project folder:** `ugc-miyou/` (La Belle Miyou was the first product)
- **Scenes config:** JSON file defining each scene's prompt, duration, voiceover

## How It Works
1. Upload avatar image to KIE
2. Generate Scene 1 video from avatar image via Kling 3.0 (image-to-video)
3. Extract last frame of Scene 1
4. Upload last frame → generate Scene 2 from it (scene chaining)
5. Repeat for all scenes
6. Generate voiceover with ElevenLabs (Liam voice — young, energetic)
7. Stitch all scenes + voiceover with ffmpeg

## Key Technique: Scene Chaining
Each scene uses the **last frame of the previous scene** as its starting image. This maintains visual consistency (same person, same setting) across multiple scenes without needing a reference video.

## API: KIE (kie.ai)
- **Model:** `kling-3.0/video`
- **Endpoint:** `POST https://api.kie.ai/api/v1/jobs/createTask`
- **Upload:** `POST https://kieai.redpandaai.co/api/file-stream-upload`
- **Poll:** `GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...`
- **Auth:** `Bearer {KIE_API_KEY}`
- **Mode:** `pro` (1080p) or `std` (720p)
- **Duration:** 3-15 seconds per scene
- **Aspect ratio:** `9:16` for vertical (TikTok/Reels)
- **Cost:** ~$0.10-0.15/sec → ~$3-5 per 30s video

### KIE Task Body Format (Kling 3.0)
```json
{
  "model": "kling-3.0/video",
  "input": {
    "prompt": "motion description",
    "image_urls": ["start_image_url"],
    "mode": "pro",
    "aspect_ratio": "9:16",
    "duration": "10",
    "multi_shots": false,
    "multi_prompt": [],
    "sound": false
  }
}
```

## Usage
```bash
python3 execution/generate_ugc_video.py \
  --avatar path/to/avatar.jpg \
  --product path/to/product.jpg \
  --output-dir output/ \
  --scenes scenes.json \
  --mode pro \
  --scene-index 0  # optional: test single scene
```

## Scene JSON Format
```json
[
  {
    "name": "hook",
    "prompt": "description of motion and setting",
    "duration": 5,
    "voiceover": "What the person says in this scene",
    "use_product": false
  }
]
```

## Cost Warning
- Kling 3.0 Pro via KIE: ~$0.10-0.15/sec
- A 5-scene, 38-second video costs ~$4-6
- Always test with `--scene-index 0` first before full run
- Consider `--mode std` (720p) for drafts to save money

## Paused — Exploring Cheaper Alternatives
Pipeline works but cost per video is high ($3-5). Need to find cheaper image-to-video APIs or use a different approach before scaling.

## MANDATORY: Agent Team Scene Planning (Read Before Every Run)

**Problem discovered 2026-02-23:** Kling 3.0 image-to-video does NOT create new environments. It animates the input image as-is. If you feed it a plain avatar headshot, you get a headshot with slight motion — not a gym scene, not a kitchen, not anything new. The model treats the image as the entire scene.

**Solution:** Before ANY video generation, run an Agent Team to plan each scene in full creative detail. The team must figure out:

1. **Script & Story Arc** — What's the hook? What's the narrative beat per scene? What's the CTA?
2. **Per-Scene Creative Brief:**
   - Exact background/environment description
   - Camera angle & movement (close-up, wide, tracking, etc.)
   - Actor actions & expressions (not just "standing there")
   - Lighting & mood
   - Props visible in frame
   - How the product appears
3. **Prompt Engineering** — Translate the creative brief into a Kling 3.0 prompt that will actually produce the desired scene. The prompt must describe the FULL frame (environment + person + action + lighting), not just the person.
4. **Scene Continuity** — Plan how scenes chain visually (last frame of scene N → starting point of scene N+1)

### Agent Team Roles

| Agent | Job |
|-------|-----|
| **Creative Director** | Plans the overall story arc, pacing, and shot list. Writes the voiceover script. |
| **Scene Designer** | For each scene: designs the environment, camera angle, lighting, and action. Writes the detailed Kling prompt. |
| **Pipeline Runner** | Takes the finalized scene JSON and runs `generate_ugc_video.py`. Monitors costs. |

### Workflow
1. Creative Director plans story + voiceover script
2. Scene Designer takes each beat and writes a full creative brief + Kling prompt
3. Team reviews all prompts for continuity and quality
4. Pipeline Runner generates the video
5. Review output, log what worked / didn't

### Prompt Rules (Learned the Hard Way)
- **DO:** Describe the full environment in every prompt ("modern gym with weight racks, mirrors, overhead fluorescent lights")
- **DO:** Describe the person's action in detail ("doing heavy dumbbell curls with controlled powerful movements")
- **DO:** Include lighting, mood, camera feel ("raw authentic phone video UGC feel, overhead lighting")
- **DON'T:** Assume Kling will create a setting from nothing — it won't
- **DON'T:** Use vague prompts like "man in gym" — be specific about what's IN the frame
- **DON'T:** Expect the avatar photo alone to produce a scene — the avatar is just a face/body reference, the prompt must paint the entire picture

## Error Log

### [2026-02-23] Avatar-only scenes — Kling just animated the avatar photo instead of creating a real scene
- **What happened:** The product was a collagen supplement. Scene 1 needed the guy to be in a gym. Instead, Kling just took the avatar headshot photo and added slight motion/wobble to it — the output was literally the same static avatar image with the face moving slightly. No gym, no weights, no environment. Just the photo animating in place.
- **Why:** Kling 3.0 image-to-video treats the input image as the complete scene and adds motion to it. It does NOT place the person into a new environment. Whatever the input image looks like IS the scene — so a headshot against a plain background stays a headshot against a plain background.
- **Fix:** Scenes must be planned by an Agent Team before generation. Each prompt must describe the FULL frame (environment + person + action + lighting). The avatar is a face/body reference, not a scene.
- **Rule:** NEVER run the pipeline without the Agent Team planning phase. Every scene needs a full creative brief and a prompt that paints the entire frame. Read the "MANDATORY: Agent Team Scene Planning" section above before every run.

### Previous Errors
- `mode "1080p"` is invalid for Kling 3.0 on KIE → use `"pro"` or `"std"`
- `multi_shots cannot be empty` → KIE Kling 3.0 requires `multi_shots: false` (boolean), not omitted
- `prompt` goes inside `input`, not at top level (unlike Kling 2.6 motion control)
- `duration` must be a string (`"10"`), not an integer
