#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Lead Generation video via KIE API.

Usage:
  python3 execution/generate_leadgen_sfx.py

Output:
  yt-growth-chart/public/sfx-leadgen/sfx_00.mp3 ... sfx_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-leadgen"

SFX_PROMPTS = [
    "computer keyboard clicking with browser page loading and mouse scrolling sounds",
    "slow tedious typing on keyboard with paper shuffling and frustrated sigh",
    "water draining from pipe with descending tone and empty echo",
    "futuristic AI radar sweep with scanning pulse and discovery chime",
    "rapid data processing with card sorting sounds and digital filtering whoosh",
    "score meter filling with gauge ticking and positive evaluation tone",
    "data enrichment sparkle with contact card stamping and verification ding",
    "smooth pipeline flow with items dropping into place and CRM notification chime",
    "counter rapidly incrementing with impressed crowd gasp and success fanfare",
    "cash register price dropping with coins saved and celebration bell",
    "racing countdown with competitive tension building and urgency alarm",
    "rocket launch ignition with pipeline filling up and notification sparkle burst",
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
