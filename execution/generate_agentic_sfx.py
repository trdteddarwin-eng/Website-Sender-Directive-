#!/usr/bin/env python3
"""
Generate per-scene sound effects for Agentic Workflow video using Replicate AudioGen.

Usage:
  python execution/generate_agentic_sfx.py

Output:
  yt-growth-chart/public/sfx-agentic/sfx_00.wav ... sfx_14.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-agentic"

# Per-scene SFX prompts matched to Agentic Workflow video scenes
SFX_SCENES = [
    {"prompt": "mechanical robot arm servo clicking and whirring, industrial automation", "duration": 3},
    {"prompt": "hamster wheel spinning faster and faster with squeaky metal sound", "duration": 3},
    {"prompt": "heavy thud impact revealing disappointing statistic, dramatic reveal", "duration": 3},
    {"prompt": "water dripping through cracks, liquid leaking away slowly", "duration": 3},
    {"prompt": "futuristic AI power up activation with digital synth ascending tone", "duration": 3},
    {"prompt": "detective magnifying glass scanning with electronic search beeps", "duration": 3},
    {"prompt": "pen writing quickly on paper with email whoosh send sound", "duration": 3},
    {"prompt": "precision clock tick with perfect timing chime, well-timed alert", "duration": 3},
    {"prompt": "calendar page flip with booking confirmation chime, nighttime ambient", "duration": 3},
    {"prompt": "cash register ching with downward cost savings tone, efficient", "duration": 3},
    {"prompt": "steady reliable server humming continuously, always-on machine", "duration": 3},
    {"prompt": "neural network synapses firing with ascending intelligence sparkle", "duration": 3},
    {"prompt": "rocket launching in distance while stuck engine sputters, competitive gap", "duration": 3},
    {"prompt": "money burning with fire crackle and coins dropping, loss", "duration": 3},
    {"prompt": "rocket engine ignition building to powerful liftoff with sparkle trail", "duration": 3},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.wav")

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

        time.sleep(12.0)  # rate limit: 6 req/min with <$5 credit

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")]
    print(f"\nDone! Generated {len(generated)}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
