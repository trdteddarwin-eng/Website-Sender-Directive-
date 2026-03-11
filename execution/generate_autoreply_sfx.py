#!/usr/bin/env python3
"""
Generate per-scene sound effects for Automatic Email Reply video via KIE API.

Usage:
  python3 execution/generate_autoreply_sfx.py

Output:
  yt-growth-chart/public/sfx-autoreply/sfx_00.mp3 ... sfx_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-autoreply"

SFX_PROMPTS = [
    "email notification ping at night with phone vibration buzz",
    "clock ticking slowly with crickets at night then sunrise birds chirping",
    "racing starting gun with competitive footsteps rushing and door opening",
    "futuristic AI activation with keyboard typing burst and email send whoosh",
    "document scanning with text highlighting sound and classification sorting click",
    "pen writing smoothly with paper slide and style matching confirmation tone",
    "multiple task completion dings with calendar booking chime and question mark pop",
    "sorting conveyor belt with priority alarm for urgent and smooth auto-handle sound",
    "timer rapidly counting down from high number with speed acceleration whoosh",
    "upward trending chart sound with percentage climbing and success celebration bell",
    "clock ticking with urgency building and coins dropping away one by one",
    "rocket engine ignition with email notification sparkle and power-up launch sound",
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating SFX for {len(SFX_PROMPTS)} scenes via KIE API...")
    print(f"Model: elevenlabs/sound-effect-v2\n")

    for i, prompt in enumerate(SFX_PROMPTS):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue
        print(f"  Scene {i:2d}: \"{prompt[:60]}\"", end="", flush=True)
        size = generate_sfx(prompt, 3.0, output_path)
        if size:
            print(f" -> {size:.1f}KB")
        else:
            print(" FAILED")

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! {len(generated)}/{len(SFX_PROMPTS)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
