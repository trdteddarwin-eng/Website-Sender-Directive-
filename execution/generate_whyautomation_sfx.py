#!/usr/bin/env python3
"""
Generate per-scene sound effects for WhyAutomation video using Replicate AudioGen.

Usage:
  python execution/generate_whyautomation_sfx.py

Output:
  tiktok-recreation/public/sfx-whyautomation/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-whyautomation"

SFX_SCENES = [
    {"prompt": "old typewriter clicking slowly with paper rustling, vintage office atmosphere", "duration": 2.5},
    {"prompt": "rapid keyboard typing accelerating faster and faster, digital speed", "duration": 2.5},
    {"prompt": "mechanical repetitive clicking sound, factory assembly line, monotonous rhythm", "duration": 2.5},
    {"prompt": "heavy thud impacts in sequence, items dropping one by one, weighty", "duration": 2.5},
    {"prompt": "sand pouring through hourglass steadily, time passing, granular flow", "duration": 2.5},
    {"prompt": "satisfying mechanical switch click with electrical power up hum, activation", "duration": 2.5},
    {"prompt": "gentle electronic humming power on with soft robotic beep, futuristic", "duration": 2.5},
    {"prompt": "digital stopwatch ticking with notification ping alert, precise timing", "duration": 2.5},
    {"prompt": "soft chime notification sounds in sequence, pleasant digital alerts", "duration": 2.5},
    {"prompt": "cash register cha-ching with coin sounds, money and success", "duration": 2.5},
    {"prompt": "dramatic ascending whoosh rising upward, growth and momentum, powerful", "duration": 2.5},
    {"prompt": "magical sparkle chime with time reversal whoosh, enchanting and bright", "duration": 2.5},
    {"prompt": "multiple racing swooshes accelerating past, competitive robots rushing forward", "duration": 2.5},
    {"prompt": "ticking clock with rising tension, urgency building, dramatic countdown", "duration": 2.5},
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
