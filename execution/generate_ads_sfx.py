#!/usr/bin/env python3
"""
Generate per-scene sound effects for Good vs Bad Ads video using Replicate AudioGen.

Usage:
  python execution/generate_ads_sfx.py

Output:
  tiktok-recreation/public/sfx-ads/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-ads"

# Per-scene SFX prompts matched to visual animations
SFX_SCENES = [
    {"prompt": "deep cinematic bass drop with subtle suspenseful riser tone, dark atmospheric", "duration": 2.0},
    {"prompt": "glass shards falling and scattering on hard surface, distant and muffled", "duration": 2.0},
    {"prompt": "smooth swoosh whoosh sound moving left to right, clean and airy", "duration": 1.5},
    {"prompt": "multiple objects clattering and colliding together chaotically, paper shuffling mess", "duration": 2.0},
    {"prompt": "soft single chime bell tone, clean and resonant, peaceful clarity", "duration": 1.5},
    {"prompt": "faint distant tap barely audible, weak and thin, quiet electronic blip fading out", "duration": 1.5},
    {"prompt": "powerful confident click followed by bright shimmering sparkle burst, satisfying", "duration": 2.0},
    {"prompt": "harsh digital glitch noise with stuttering static interference, chaotic electronic", "duration": 2.0},
    {"prompt": "gentle flowing water stream, smooth and calming, soft ambient white noise", "duration": 2.0},
    {"prompt": "heavy rubber stamp slamming down on paper, firm thud impact", "duration": 1.5},
    {"prompt": "camera shutter click followed by soft warm confirmation tone", "duration": 1.5},
    {"prompt": "crowd of overlapping voices murmuring indistinctly, confusing noise, busy static", "duration": 2.0},
    {"prompt": "single clear sonar ping followed by bright ascending sparkle particles", "duration": 2.0},
    {"prompt": "gentle digital processing sounds with soft ascending tones, data flowing, futuristic", "duration": 2.0},
    {"prompt": "keyboard typing sounds, mechanical keys clicking rhythmically, soft and satisfying", "duration": 2.0},
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
