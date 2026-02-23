#!/usr/bin/env python3
"""
Generate per-scene sound effects for Social Media Marketing video using Replicate AudioGen.

Usage:
  python execution/generate_smm_sfx.py

Output:
  tiktok-recreation/public/sfx-smm/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-smm"

# Per-scene SFX prompts matched to Social Media Marketing video scenes
SFX_SCENES = [
    {"prompt": "eerie digital ghost whoosh, ethereal fading sound, unsettling", "duration": 2.5},
    {"prompt": "dramatic impact boom, heavy thud with reverb, alarming reveal", "duration": 2.5},
    {"prompt": "three quick error buzzes, digital rejection sounds, negative feedback", "duration": 2.5},
    {"prompt": "coins clinking with footsteps walking away, money leaving, loss", "duration": 2.5},
    {"prompt": "powerful electric zap with energy surge, transformation moment", "duration": 2.5},
    {"prompt": "magnetic pull whoosh with gentle suction, attracting objects inward", "duration": 2.5},
    {"prompt": "upward swoosh followed by notification chime, growth and engagement", "duration": 2.5},
    {"prompt": "arrow thud hitting target with satisfying impact, precision hit", "duration": 2.5},
    {"prompt": "confident power up chime, shield activation, trust building tone", "duration": 2.5},
    {"prompt": "dramatic ascending orchestral swell, impressive reveal, powerful crescendo", "duration": 2.5},
    {"prompt": "cash register cha-ching with coins stacking, money multiplying, profit", "duration": 2.5},
    {"prompt": "epic achievement fanfare with sparkle burst, triumphant celebration", "duration": 2.5},
    {"prompt": "rapid typing and multiple notification ping sounds, busy social media activity", "duration": 2.5},
    {"prompt": "fire crackling and burning intensely, destructive flames consuming", "duration": 2.5},
    {"prompt": "keyboard typing then rocket engine ignition with ascending sparkle trail", "duration": 2.5},
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
