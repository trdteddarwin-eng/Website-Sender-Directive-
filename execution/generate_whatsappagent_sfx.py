#!/usr/bin/env python3
"""
Generate per-scene sound effects for WhatsApp Agent video via KIE API.

Usage:
  python3 execution/generate_whatsappagent_sfx.py

Output:
  yt-growth-chart/public/sfx-whatsappagent/sfx_00.mp3 ... sfx_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-whatsappagent"

SFX_PROMPTS = [
    "smartphone notification ping message received with gentle vibration buzz",
    "clock ticking slowly getting louder with silence and empty room echo",
    "message whoosh sound flying away, door closing, missed opportunity",
    "coins dropping and scattering on floor, cash register closing empty",
    "futuristic AI power up surge with electric spark and hopeful ascending tone",
    "digital neural network connecting nodes with soft electronic pulses",
    "clear chat message send and receive sounds with soft keyboard typing",
    "calendar appointment booking confirmation chime with pen writing on paper",
    "multiple notification pings overlapping rapidly like busy chat system",
    "crowd cheering softly with success bell and upward climbing tone",
    "racing countdown timer beeping fast with urgency building tension",
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
