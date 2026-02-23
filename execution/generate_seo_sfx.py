#!/usr/bin/env python3
"""
Generate per-scene sound effects for SEO video using Replicate AudioGen.

Usage:
  python execution/generate_seo_sfx.py

Output:
  tiktok-recreation/public/sfx-seo/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-seo"

# Per-scene SFX prompts matched to visual animations
SFX_SCENES = [
    {"prompt": "deep dark ambient void drone, empty space, low rumbling atmosphere fading in", "duration": 2.0},
    {"prompt": "keyboard typing sounds, mechanical keys clicking rapidly, soft and clean", "duration": 2.0},
    {"prompt": "smooth ethereal whoosh dissolving into silence, airy fade out", "duration": 2.0},
    {"prompt": "coins and metal objects dropping on table then abrupt silence, sudden stop", "duration": 2.0},
    {"prompt": "bright ascending chime tones rising progressively higher, hopeful crescendo", "duration": 2.0},
    {"prompt": "multiple swoosh sounds racing past quickly, wind rushing left to right", "duration": 2.0},
    {"prompt": "slow tension stretching sound, rubber band pulling taut, ominous growing distance", "duration": 2.0},
    {"prompt": "harsh digital glitch noise with stuttering static interference, chaotic electronic", "duration": 2.0},
    {"prompt": "soft triple chime confirmation tones, clean and warm, gentle bell sequence", "duration": 1.5},
    {"prompt": "heavy rubber stamp slamming down on paper, firm thud impact, authoritative", "duration": 1.5},
    {"prompt": "metallic key turning in lock click followed by bright shimmering sparkle burst", "duration": 2.0},
    {"prompt": "single sonar ping with expanding echo ripple, radar pulse, location found", "duration": 2.0},
    {"prompt": "solid shield impact clang followed by soft buzzer warning tone", "duration": 2.0},
    {"prompt": "clock ticking accelerating then smooth forward whoosh, time moving", "duration": 2.0},
    {"prompt": "rocket launch ascending with bright sparkle trail, powerful upward thrust", "duration": 2.0},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.mp3")

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

        time.sleep(1.0)

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! Generated {len(generated)}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
