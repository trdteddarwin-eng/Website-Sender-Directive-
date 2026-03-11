#!/usr/bin/env python3
"""
Generate per-scene sound effects for Auto Follow-Up Email video via KIE API.

Usage:
  python3 execution/generate_followupemail_sfx.py

Output:
  yt-growth-chart/public/sfx-followupemail/sfx_00.mp3 ... sfx_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-followupemail"

SFX_PROMPTS = [
    "email sending whoosh with soft keyboard click and envelope paper slide",
    "clock ticking slowly with dust settling and empty silence tension",
    "pen signing on paper with door closing and footsteps walking away",
    "coins dropping and funnel draining with declining tone descending",
    "futuristic AI power up surge with magical sparkle and email notification chime",
    "keyboard typing rapidly with multiple email send whooshes and soft AI processing hum",
    "clock chime with precision tick and email notification at perfect moment",
    "smooth transition tones ascending from cold to warm with gentle bell progression",
    "rapid fire email send sounds overlapping with busy office automation hum",
    "cash register opening with success fanfare and upward climbing celebration tone",
    "racing countdown timer beeping with urgency building competitive tension",
    "rocket engine ignition with ascending power and email notification sparkle launch",
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
