#!/usr/bin/env python3
"""
Generate narration audio for AI Lead Scoring video via KIE API.

Usage:
  python3 execution/generate_leadscore_narration.py

Output:
  yt-growth-chart/public/narration-leadscore/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-leadscore"

SCENES = [
    "[matter-of-fact] Monday morning. Fifty new leads hit your pipeline.",
    "[matter-of-fact] Your closer sits down, opens the CRM, and... starts guessing. Who do I call first?",
    "[serious] Four hours later — they've been chasing a tire-kicker who was never going to buy. Meanwhile, the CEO who visited your pricing page THREE times? [short pause] Gone.",
    "[serious] Sixty-seven percent of sales time gets wasted on leads that will NEVER close. [pause] That's four hours a day, burned.",
    "[excited] So we built a scoring engine that ranks every lead the second they come in.",
    "[confident] It looks at everything — page visits, email opens, company size, buying signals — and spits out a score from one to a hundred.",
    "[confident] Your hottest leads go straight to your closers. No guessing. No spreadsheet sorting. Just the RIGHT call, FIRST.",
    "[excited] And cold leads? They don't get ignored — they get dropped into a nurture sequence until they're ready to buy.",
    "[matter-of-fact] One B2B agency plugged this in. [short pause] First week, their reps stopped wasting mornings on dead leads and started closing by lunch.",
    "[excited] Fifty percent more conversions. [pause] Same team, same product — they just finally knew WHO to call.",
    "[serious] Without scoring, your closers are spending four hours a day on leads that will never buy. [short pause] That's not a pipeline — that's a money pit.",
    '[excited] DM leadscore — and put your best leads at the top where they belong.',
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating narration for {len(SCENES)} scenes via KIE API...")
    print(f"Voice: Liam (elevenlabs/text-to-dialogue-v3)\n")

    durations = []
    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue
        clean = text.replace("[", "").replace("]", "")[:50]
        print(f"  Scene {i:2d}: \"{clean}\"", end="", flush=True)
        dur = generate_narration(text, output_path)
        if dur:
            durations.append(round(dur, 3))
            print(f" -> {dur:.2f}s")
        else:
            durations.append(3.0)
            print(" FAILED")

    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")])
    print(f"\nDone! {total}/{len(SCENES)} narration files in {OUTPUT_DIR}/")
    if durations:
        print(f"AUDIO_DURATIONS = [{', '.join(str(d) for d in durations)}]")


if __name__ == "__main__":
    main()
