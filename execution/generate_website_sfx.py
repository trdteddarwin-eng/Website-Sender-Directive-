#!/usr/bin/env python3
"""
Generate per-scene sound effects for Website video using Replicate AudioGen.

Usage:
  python execution/generate_website_sfx.py

Output:
  tiktok-recreation/public/sfx-website/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-website"

# Per-scene SFX prompts matched to visual animations
SFX_SCENES = [
    {"prompt": "dramatic suspenseful hit with deep reverb, shocking reveal impact, cinematic", "duration": 2.0},
    {"prompt": "multiple footsteps searching and wandering, people walking around looking", "duration": 2.0},
    {"prompt": "smooth swoosh moving past, opportunity flying by, wind rushing", "duration": 2.0},
    {"prompt": "digital notification sounds fading and becoming muffled, losing signal", "duration": 2.0},
    {"prompt": "heavy padlock snapping shut, metallic chain rattling, locked away", "duration": 1.5},
    {"prompt": "electrical power down sound, system shutting off, descending tone to silence", "duration": 2.0},
    {"prompt": "steady mechanical ticking rhythm, clockwork running smoothly, reliable engine", "duration": 2.0},
    {"prompt": "continuous soft heartbeat pulse, steady and strong, alive rhythm", "duration": 2.0},
    {"prompt": "glass cracking and breaking apart, fragile structure collapsing", "duration": 1.5},
    {"prompt": "bright ascending chime with shimmering sparkle, achievement unlocked, positive", "duration": 2.0},
    {"prompt": "cash register ching followed by confident speech bubble pop", "duration": 1.5},
    {"prompt": "triple soft confirmation chimes ascending, questions resolving, clarity", "duration": 2.0},
    {"prompt": "coins slowly dropping and rolling away, money escaping, fading metallic", "duration": 2.0},
    {"prompt": "multiple racing swooshes accelerating ahead, competitive rushing forward", "duration": 2.0},
    {"prompt": "rocket launch ignition ascending with bright sparkle trail, powerful liftoff", "duration": 2.0},
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
