#!/usr/bin/env python3
"""
Generate per-scene sound effects for Email Automation video using Replicate AudioGen.

Usage:
  python execution/generate_email_sfx.py

Output:
  tiktok-recreation/public/sfx-email/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-email"

# Per-scene SFX prompts matched to Email Automation video scenes
SFX_SCENES = [
    {"prompt": "email notification sound fading into emptiness, lost opportunity, subtle and ominous", "duration": 2.5},
    {"prompt": "slow heavy clock ticking with warning alarm undertone, time wasted", "duration": 2.5},
    {"prompt": "footsteps walking away on hard floor, door closing shut, departure", "duration": 2.5},
    {"prompt": "stopwatch click start with tense ticking, precise and focused", "duration": 2.5},
    {"prompt": "explosive upward whoosh with triumphant sparkle burst, big reveal", "duration": 2.5},
    {"prompt": "overwhelming overlapping notification sounds, chaotic buzzing, stress", "duration": 2.5},
    {"prompt": "smooth futuristic scanning sound then clean confirmation chime, AI processing", "duration": 2.5},
    {"prompt": "soft keyboard typing with gentle message sent whoosh, personalized feel", "duration": 2.5},
    {"prompt": "fast countdown beeping then satisfying completion ding, speed and precision", "duration": 2.5},
    {"prompt": "calendar page flipping rapidly with soft scheduling clicks, organized", "duration": 2.5},
    {"prompt": "safety net catch sound, secure hold, reliable protection tone", "duration": 2.5},
    {"prompt": "cash register ching with energetic power-up hum, money machine activated", "duration": 2.5},
    {"prompt": "gentle nighttime ambiance with soft robot working sounds, peaceful productivity", "duration": 2.5},
    {"prompt": "multiple racing swooshes accelerating ahead, competitive robots rushing forward", "duration": 2.5},
    {"prompt": "rocket engine ignition building to powerful liftoff with ascending sparkle trail", "duration": 2.5},
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
