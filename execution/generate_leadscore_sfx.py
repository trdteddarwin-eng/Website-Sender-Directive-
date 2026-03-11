#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Lead Scoring video via KIE API.

Usage:
  python3 execution/generate_leadscore_sfx.py

Output:
  yt-growth-chart/public/sfx-leadscore/sfx_00.mp3 ... sfx_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-leadscore"

SFX_PROMPTS = [
    "digital notification chime with data entry ping and pipeline flowing water",
    "confused searching sounds with papers shuffling and question mark suspense",
    "ice cracking with cold wind and opportunity door slowly closing",
    "coins dropping and clock ticking wasted time with declining tone",
    "futuristic AI power up surge with magical scoring calculation sparkle",
    "digital data streams processing with neural network soft electronic pulses",
    "speedometer gauge filling with precision meter click and score reveal chime",
    "priority alert bell with fire crackling and urgent ascending tone",
    "smooth routing whoosh with connection established confirmation tone",
    "crowd cheering with success fanfare and upward climbing celebration",
    "racing countdown timer with competitive tension building urgency",
    "rocket engine ignition with ascending power and sparkle trail launch",
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
