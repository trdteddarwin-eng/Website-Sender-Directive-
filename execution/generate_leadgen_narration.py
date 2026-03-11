#!/usr/bin/env python3
"""
Generate narration audio for AI Lead Generation video via KIE API.

Usage:
  python3 execution/generate_leadgen_narration.py

Output:
  yt-growth-chart/public/narration-leadgen/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-leadgen"

SCENES = [
    "[matter-of-fact] You're on Google Maps. Scrolling through roofing companies in Dallas — copying names into a spreadsheet, one by ONE.",
    "[matter-of-fact] An hour goes by. You've got... twelve leads. [pause] Maybe eight have emails.",
    "[serious] Meanwhile, your pipeline's drying up. Deals aren't closing because there's nothing TO close.",
    "[serious] And every one of those leads? You're paying twelve to fifteen dollars EACH — if you're lucky.",
    "[excited] So we built a machine that does this while you sleep. Not in hours — in MINUTES.",
    "[confident] You set your criteria — industry, location, revenue, employee count. It scans THOUSANDS of businesses and pulls the ones that actually fit.",
    "[confident] Then it enriches every single one — verified email, phone number, decision-maker name and TITLE.",
    "[excited] Qualified leads land in your CRM, scored and ready to contact — before you've had your morning coffee.",
    "[matter-of-fact] One agency ran this for forty-eight hours. [pause] Four hundred leads. Verified. Scored. Ready to GO.",
    "[excited] Their cost per lead went from twelve dollars... to a dollar FIFTY.",
    "[serious] Right now, you're spending hours on work a machine does in minutes. [pause] And every lead you don't find — your competitor already HAS.",
    '[excited] DM leadgen — and fill your pipeline for the price of a cup of coffee.',
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
