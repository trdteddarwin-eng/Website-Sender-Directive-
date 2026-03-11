#!/usr/bin/env python3
"""
Generate narration audio for AI Chatbot video via KIE API.

Usage:
  python3 execution/generate_chatbot_narration.py

Output:
  yt-growth-chart/public/narration-chatbot/scene_00.mp3 ... scene_14.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-chatbot"

SCENES = [
    "[matter-of-fact] Someone lands on your website at two AM. They're interested — credit card practically OUT.",
    "[matter-of-fact] They type a question into your chat box... and nothing. No one's there.",
    "[serious] Ten seconds go by. Twenty. [pause] They close the tab.",
    "[serious] Gone. -- -- You never even knew they were there.",
    "[matter-of-fact] Here's the painful part — fifty-three percent of visitors bounce if no one replies within TEN seconds.",
    "[serious] That's not a support problem. That's a revenue LEAK.",
    "[excited] So we built something. An AI that sits on your site — twenty-four seven — and actually SELLS.",
    "[confident] A visitor asks about pricing? It pulls your real numbers. Gives a straight answer.",
    "[confident] Someone's comparing you to a competitor? It handles the OBJECTION — live, in the chat.",
    "[excited] It captures their name, email, and books the meeting — all inside the CONVERSATION.",
    "[matter-of-fact] No forms. No friction. Just a visitor who came curious and left with an appointment on your calendar.",
    "[matter-of-fact] One med spa added this to their site. [pause] Thirty-five percent more consultations booked — in the first MONTH.",
    "[excited] That's leads that were already coming to their site... just finally getting CAUGHT.",
    "[serious] Every hour your site runs without this, qualified buyers are landing, looking around... and walking away with their wallets.",
    "[excited] DM chatbot — and stop losing the leads you already PAID for.",
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
