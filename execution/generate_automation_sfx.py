#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Automation video using Replicate AudioGen.

Usage:
  python execution/generate_automation_sfx.py

Output:
  tiktok-recreation/public/sfx-automation/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-automation"

# Per-scene SFX prompts matched to AI automation video scenes
SFX_SCENES = [
    {"prompt": "slow dripping liquid sound, blood dropping, ominous and unsettling, dark", "duration": 2.5},
    {"prompt": "heavy impact thud with cash register error beep, costly mistake, alarming", "duration": 2.5},
    {"prompt": "soft paper rustling and pen writing sounds, gentle office ambiance", "duration": 2.5},
    {"prompt": "ticking clock accelerating faster and faster, time pressure building, urgent", "duration": 2.5},
    {"prompt": "sharp electric zap followed by smooth futuristic processing hum, fast and clean", "duration": 2.5},
    {"prompt": "mechanical robot servo activating with confident power-up tone, efficient machine", "duration": 2.5},
    {"prompt": "soft digital notification chime, gentle and brief, clean message tone", "duration": 2.5},
    {"prompt": "fast-forward tape rewind sound then clean completion ding, speed processing", "duration": 2.5},
    {"prompt": "bright notification ping followed by satisfying confirmation tone, reliable alert", "duration": 2.5},
    {"prompt": "dramatic ascending orchestral swell, impressive reveal, powerful crescendo", "duration": 2.5},
    {"prompt": "cash register ching followed by coin stacking sounds, money accumulating", "duration": 2.5},
    {"prompt": "explosive sparkle burst with triumphant fanfare hit, celebration achievement", "duration": 2.5},
    {"prompt": "multiple racing swooshes accelerating ahead, competitive robots rushing forward", "duration": 2.5},
    {"prompt": "fire crackling and burning intensely, money on fire, destructive flames", "duration": 2.5},
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
