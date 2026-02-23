#!/usr/bin/env python3
"""
Generate per-scene sound effects for Why Ads video using Replicate AudioGen.

Usage:
  python execution/generate_whyads_sfx.py

Output:
  tiktok-recreation/public/sfx-whyads/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-whyads"

# Per-scene SFX prompts matched to Why Ads video scenes
SFX_SCENES = [
    {"prompt": "lonely wind blowing through empty store, crickets chirping, abandoned silence", "duration": 2.5},
    {"prompt": "dice rolling on table and landing flat, uncertain gamble, disappointing result", "duration": 2.5},
    {"prompt": "heavy coins dropping and stacking rapidly, big money being spent, competitive", "duration": 2.5},
    {"prompt": "slow ticking clock with cobweb sounds, dusty and stale, time wasting away", "duration": 2.5},
    {"prompt": "people footsteps fading into distance one by one, missed connections, leaving", "duration": 2.5},
    {"prompt": "bullseye arrow hitting target dead center, precise impact, satisfying thud", "duration": 2.5},
    {"prompt": "shopping cart click with perfect timing chime, instant purchase moment", "duration": 2.5},
    {"prompt": "coin going into slot machine then double coins pouring out, multiplied return", "duration": 2.5},
    {"prompt": "social media notification sounds layered with upward swoosh, growth acceleration", "duration": 2.5},
    {"prompt": "crowd growing louder and louder, audience filling stadium, massive expansion", "duration": 2.5},
    {"prompt": "futuristic scanning lock-on sound with data processing beeps, precision targeting", "duration": 2.5},
    {"prompt": "smooth slider control moving upward with power increase hum, scaling energy", "duration": 2.5},
    {"prompt": "storefront shutters closing with sad decline sound, going dark, fading away", "duration": 2.5},
    {"prompt": "urgent alarm clock ringing with calendar page ripping, time running out", "duration": 2.5},
    {"prompt": "eye opening sound with bright spotlight activation, visibility achieved, seen", "duration": 2.5},
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
