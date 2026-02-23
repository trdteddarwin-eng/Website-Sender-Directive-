#!/usr/bin/env python3
"""
Generate per-scene sound effects for SmartAI video using Replicate AudioGen.

Usage:
  python execution/generate_smartai_sfx.py

Output:
  tiktok-recreation/public/sfx-smartai/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-smartai"

SFX_SCENES = [
    {"prompt": "dramatic tension hit with low rumble, bar chart dropping, failure sound, dark and ominous", "duration": 2.5},
    {"prompt": "deep bass rumble with intimidating stomp, giant approaching, heavy footsteps", "duration": 2.5},
    {"prompt": "ticking clock accelerating faster and faster, time pressure building, urgent countdown", "duration": 2.5},
    {"prompt": "suspenseful reveal sound with subtle light bulb ding, mystery uncovered, gentle epiphany", "duration": 2.5},
    {"prompt": "mechanical robot servo whir followed by confident power-up tone, machine activation", "duration": 2.5},
    {"prompt": "uplifting whoosh with balance scale settling, equilibrium achieved, satisfying resolution", "duration": 2.5},
    {"prompt": "digital transformation sound, multiple nodes merging into one, futuristic compression", "duration": 2.5},
    {"prompt": "quick notification chime cascade, emails clearing rapidly, clean inbox sound", "duration": 2.5},
    {"prompt": "electric zap with lightning crack, instant and powerful, energetic bolt strike", "duration": 2.5},
    {"prompt": "gentle ambient hum with soft chime, peaceful nighttime, calm automated process", "duration": 2.5},
    {"prompt": "powerful energy surge with ascending sparkle, multiplier effect, level-up achievement", "duration": 2.5},
    {"prompt": "energetic whoosh with rapid checkmarks, nonstop momentum, continuous motion", "duration": 2.5},
    {"prompt": "triumphant ascending swell, victory fanfare, success and growth celebration", "duration": 2.5},
    {"prompt": "warning alarm with declining tone, flatline beep, failure and descent", "duration": 2.5},
    {"prompt": "confident rocket ignition building to liftoff with ascending sparkle trail, launch", "duration": 2.5},
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
