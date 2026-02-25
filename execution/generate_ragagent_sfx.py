#!/usr/bin/env python3
"""
Generate per-scene ambient SFX for RAG Agent video using Replicate AudioGen.

Usage:
  export $(grep -v '^#' .env | xargs) && python3 execution/generate_ragagent_sfx.py

Output:
  yt-growth-chart/public/sfx-ragagent/sfx_00.wav ... sfx_11.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-ragagent"

# 12 scenes — subtle, professional ambient sounds (5s each)
SFX_SCENES = [
    {"prompt": "soft office ambient with gentle notification pings", "duration": 5},
    {"prompt": "gentle keyboard typing with quiet search whoosh", "duration": 5},
    {"prompt": "soft data visualization chime with digital ambient", "duration": 5},
    {"prompt": "quiet clock ticking with papers shuffling ambient", "duration": 5},
    {"prompt": "clean tech reveal with gentle synth pad swell", "duration": 5},
    {"prompt": "soft paper shuffling with digital processing hum", "duration": 5},
    {"prompt": "gentle neural network ambient with warm hum", "duration": 5},
    {"prompt": "clean message notification with subtle confirmation", "duration": 5},
    {"prompt": "satisfying UI toggle with clean transition sound", "duration": 5},
    {"prompt": "soft ascending tone with gentle ambient growth", "duration": 5},
    {"prompt": "subtle tension ambient with quiet competitive tone", "duration": 5},
    {"prompt": "clean startup chime with hopeful ambient swell", "duration": 5},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    generated = 0
    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.wav")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{scene['prompt'][:60]}\" ({scene['duration']}s)", end="", flush=True)
        try:
            size = generate_sfx(scene["prompt"], scene["duration"], output_path)
            print(f" -> {size:.1f}KB")
            generated += 1
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(12.0)  # rate limit: 6 req/min

    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")])
    print(f"\nDone! {total}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
