#!/usr/bin/env python3
"""
Generate a Remotion composition from TikTok video analysis.
Uses Claude Opus 4.6 via OpenRouter to create a .tsx file matching TikTokVideo.tsx architecture.

Usage:
  python execution/generate_remotion_composition.py [--analysis .tmp/tiktok-recreation/analysis.json]

Output:
  tiktok-recreation/src/RecreatedVideo.tsx
"""

import argparse
import json
import os
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CODE_MODEL = "anthropic/claude-opus-4-6"
PROJECT_DIR = "tiktok-recreation"


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def generate_composition(analysis, reference_tsx):
    """Send analysis + reference to Opus 4.6 for TSX generation."""

    scenes = analysis.get("scenes", [])
    global_props = analysis.get("global", {})
    video_info = analysis.get("video_info", {})

    total_duration_s = video_info.get("duration", 39)
    total_frames = int(total_duration_s * 30)
    num_scenes = len(scenes)
    # Calculate scene duration: total frames / num_scenes, accounting for overlaps
    fade_frames = 10
    sd = max(45, (total_frames + fade_frames * (num_scenes - 1)) // num_scenes)

    prompt = f"""You are an expert Remotion developer. Generate a complete React/TypeScript composition that recreates a TikTok video based on frame analysis.

## Video Info
- Duration: {total_duration_s:.1f}s
- Target FPS: 30
- Resolution: 1080x1920 (TikTok portrait)
- Total frames needed: ~{total_frames}
- Number of scenes: {num_scenes}
- Scene duration (SD): {sd} frames (~{sd/30:.1f}s each)
- Fade overlap (FADE): {fade_frames} frames

## Global Style
{json.dumps(global_props, indent=2)}

## Scene Analysis (from extracted frames)
{json.dumps(scenes, indent=2)}

## Reference Architecture

Below is an existing TikTok recreation (`TikTokVideo.tsx`) from the SAME creator (@conversion.doc). Your output MUST follow this exact same architecture:

```tsx
{reference_tsx}
```

## CRITICAL Requirements

1. **Follow the exact same architecture as TikTokVideo.tsx:**
   - Imports: `AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring, Easing` from remotion
   - `@remotion/google-fonts/Inter` for typography — call `loadFont("normal", {{ weights: ["400", "700", "900"], subsets: ["latin"] }})`
   - `TransitionSeries` with `fade` transitions from `@remotion/transitions`
   - Constants at top: `W = 1080, H = 1920, CX = W / 2, CY = H / 2, SD = {sd}, FADE = {fade_frames}`
   - `SCENES` string array with all text content
   - Shared components: `TextBlock` (fade in + slide up, fade out), `Dot` (white circle with optional glow), `GlowRing` (border circle with glow)
   - Per-scene graphic components: `G0`, `G1`, `G2`, ... — each with unique visual animations
   - `Scene` wrapper that combines black background + TextBlock + graphic
   - Main export: `export const RecreatedVideo: React.FC = () => {{ ... }}`
   - Use `<TransitionSeries>` with `<TransitionSeries.Sequence durationInFrames={{SD + FADE}}>` and `<TransitionSeries.Transition presentation={{fade()}} timing={{linearTiming({{durationInFrames: FADE}})}} />`

2. **Animation rules (from Remotion best practices):**
   - ALL animations MUST use `useCurrentFrame()` and `useVideoConfig()` — CSS animations are FORBIDDEN
   - Use `spring({{ frame, fps, config: {{ damping: 200 }} }})` for smooth entrances (no bounce)
   - Use `spring({{ frame, fps, config: {{ damping: 10 }} }})` for bouncy entrances
   - Use `interpolate(frame, [start, end], [from, to], {{ extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }})` for linear animations
   - Use `Easing.inOut(Easing.sin)` for smooth oscillations
   - Premount sequences when using `<Sequence>`: add `premountFor={{10}}`

3. **Visual style:**
   - Black (#000) background for ALL scenes
   - White (#FFFFFF) primary text color
   - Text at top ~12% of canvas, graphics in center/lower area
   - Font: Inter, weights 400/700/900
   - Glow effects via box-shadow on dots and rings

4. **Make each scene VISUALLY DISTINCT:**
   - Study the analysis for each scene's visual elements
   - Use different animation patterns per scene (spring entrance, interpolate drift, particle burst, glow sweep, etc.)
   - Include SVG icons where the analysis mentions them (create inline SVG components)
   - Use dots, rings, lines, shapes as accent elements
   - Reference the G0-G14 components in TikTokVideo.tsx for the level of detail expected

5. **Duration calculation:**
   - Each TransitionSeries.Sequence: `SD + FADE = {sd + fade_frames}` frames
   - Total = {num_scenes} * {sd + fade_frames} - {num_scenes - 1} * {fade_frames} = {num_scenes * (sd + fade_frames) - (num_scenes - 1) * fade_frames} frames
   - This should be close to {total_frames} frames

6. **Output:** Return ONLY the complete .tsx file content. No markdown fences, no explanation, no comments about the code. Just the raw TypeScript/React code starting with import statements."""

    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(10)
                print(f"  Retry attempt {attempt + 1}...")

            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CODE_MODEL,
                    "max_tokens": 16000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=420,
            )
            resp.raise_for_status()
            code = resp.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if present
            if code.startswith("```"):
                lines = code.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)

            return code

        except requests.exceptions.Timeout:
            print(f"  Timeout on attempt {attempt + 1}")
            if attempt == 2:
                raise
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise

    raise RuntimeError("All generation attempts failed")


def validate_typescript(project_dir):
    """Run tsc --noEmit to check for type errors."""
    cmd = ["npx", "tsc", "--noEmit"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=project_dir)
    return result.returncode == 0, result.stdout + result.stderr


def fix_typescript_errors(code, errors, reference_tsx):
    """Send TSX + errors back to Opus for fix."""
    prompt = f"""The following Remotion TypeScript file has compilation errors. Fix them and return the COMPLETE corrected file.

## Current code:
```tsx
{code}
```

## TypeScript errors:
```
{errors}
```

## Reference (working example of same architecture — first 4000 chars):
```tsx
{reference_tsx[:4000]}
```

Return ONLY the corrected .tsx file content. No markdown fences, no explanation. Just the code starting with import statements."""

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": CODE_MODEL,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=420,
    )
    resp.raise_for_status()
    fixed = resp.json()["choices"][0]["message"]["content"].strip()

    if fixed.startswith("```"):
        lines = fixed.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        fixed = "\n".join(lines)

    return fixed


def update_root_tsx(project_dir, total_frames):
    """Add RecreatedVideo composition to Root.tsx."""
    root_path = os.path.join(project_dir, "src", "Root.tsx")
    with open(root_path, "r") as f:
        content = f.read()

    # Check if already registered
    if "RecreatedVideo" in content:
        print("  RecreatedVideo already registered in Root.tsx")
        return

    # Add import and composition
    new_content = content.replace(
        'import { TikTokVideo } from "./TikTokVideo";',
        'import { TikTokVideo } from "./TikTokVideo";\nimport { RecreatedVideo } from "./RecreatedVideo";'
    )
    new_content = new_content.replace(
        "  );",
        f"""    <Composition
      id="RecreatedVideo"
      component={{RecreatedVideo}}
      durationInFrames={{{total_frames}}}
      fps={{30}}
      width={{1080}}
      height={{1920}}
    />
  );""",
        1  # Only replace the first occurrence
    )

    with open(root_path, "w") as f:
        f.write(new_content)
    print(f"  Updated Root.tsx with RecreatedVideo composition ({total_frames} frames)")


def main():
    parser = argparse.ArgumentParser(description="Generate Remotion composition from analysis")
    parser.add_argument("--analysis", default=".tmp/tiktok-recreation/analysis.json")
    parser.add_argument("--output", default="tiktok-recreation/src/RecreatedVideo.tsx")
    args = parser.parse_args()

    # Read inputs
    print("Reading analysis...")
    with open(args.analysis) as f:
        analysis = json.load(f)

    reference_path = os.path.join(PROJECT_DIR, "src", "TikTokVideo.tsx")
    print(f"Reading reference: {reference_path}")
    reference_tsx = read_file(reference_path)

    # Generate
    print(f"Generating composition with {CODE_MODEL}...")
    print("  (This may take 3-5 minutes for 16K token generation)")
    code = generate_composition(analysis, reference_tsx)

    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(code)
    print(f"  Written to {args.output} ({len(code)} chars, {len(code.splitlines())} lines)")

    # Update Root.tsx
    video_info = analysis.get("video_info", {})
    total_frames = int(video_info.get("duration", 39) * 30)
    update_root_tsx(PROJECT_DIR, total_frames)

    # Validate TypeScript
    print("Validating TypeScript...")
    ok, errors = validate_typescript(PROJECT_DIR)

    if not ok:
        print("  TypeScript errors found, attempting fix...")
        for fix_attempt in range(2):
            code = fix_typescript_errors(code, errors, reference_tsx)
            with open(args.output, "w") as f:
                f.write(code)
            print(f"  Fix attempt {fix_attempt + 1} written ({len(code)} chars)")

            ok, errors = validate_typescript(PROJECT_DIR)
            if ok:
                break
            print(f"  Still has errors: {errors[:500]}")

    if ok:
        print("  TypeScript compilation: PASS")
    else:
        print("  TypeScript compilation: FAIL (errors remain after 2 fix attempts)")
        print(f"  Errors:\n{errors[:2000]}")
        sys.exit(1)

    print("\nGeneration complete!")


if __name__ == "__main__":
    main()
