#!/usr/bin/env python3
"""
Generate per-scene ambient sound effects for ChillGym video using Replicate AudioGen.

Longer duration (5s) and ambient/calming prompts to match the zen vibe.

Usage:
  export $(grep -v '^#' .env | xargs) && python3 execution/generate_chillgym_sfx.py

Output:
  yt-growth-chart/public/sfx-chillgym/sfx_00.wav ... sfx_04.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-chillgym"

# Per-scene ambient SFX prompts — 5s each for longer scenes
SFX_SCENES = [
    {"prompt": "soft metallic hum with ambient gym reverb and distant weight clinking, atmospheric", "duration": 5},
    {"prompt": "slow rhythmic deep breathing with subtle heartbeat underneath, meditative calm", "duration": 5},
    {"prompt": "gentle wind chime with low pad synth drone, meditative peaceful ambient", "duration": 5},
    {"prompt": "soft electrical neural hum with warm ambient wash, gentle futuristic atmosphere", "duration": 5},
    {"prompt": "dawn birds chirping softly with warm ambient swell, hopeful sunrise atmosphere", "duration": 5},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.wav")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{scene['prompt'][:60]}\" ({scene['duration']}s)", end="", flush=True)
        try:
            size = generate_sfx(scene["prompt"], scene["duration"], output_path)
            print(f" -> {size:.1f}KB")
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(12.0)  # rate limit: 6 req/min with <$5 credit

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")]
    print(f"\nDone! Generated {len(generated)}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
