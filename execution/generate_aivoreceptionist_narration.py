#!/usr/bin/env python3
"""
Generate narration audio for Aivo Receptionist video using Google Gemini TTS.

Usage:
  export $(grep -v '^#' .env | grep -v '^$' | xargs) && python3 execution/generate_aivoreceptionist_narration.py

Output:
  yt-growth-chart/public/narration-aivoreceptionist/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys
import time
import json
import base64
import wave
import subprocess
import requests

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
OUTPUT_DIR = "yt-growth-chart/public/narration-aivoreceptionist"

# Voice: Sulafat (Warm) — natural storytelling feel
VOICE_NAME = "Sulafat"
MODEL = "gemini-2.5-flash-preview-tts"

# 12 scenes — short, punchy, speakable
SCENES = [
    "A customer calls your business at eight PM.",
    "Nobody answers. They call your competitor.",
    "Forty percent of calls happen after hours.",
    "Every missed call is revenue gone forever.",
    "Your team goes home. The calls don't stop.",
    "Meet Aivo. Your after hours AI receptionist.",
    "Answers instantly. Sounds completely human.",
    "Books appointments right on your calendar.",
    "Qualifies leads and sends you a summary.",
    "Works every night, weekend, and holiday.",
    "Your competitors already pick up after hours.",
    "DM Aivo to never miss a call again.",
]


def generate_scene_audio(text, output_path):
    """Generate TTS audio for a single scene using Google Gemini TTS."""
    # Add style direction to the prompt
    styled_text = f"Narrate this in a compelling, natural storytelling voice with energy and conviction: {text}"

    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        headers={
            "x-goog-api-key": GOOGLE_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": styled_text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": VOICE_NAME
                        }
                    }
                }
            }
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if "candidates" not in data:
        error_msg = data.get("error", {}).get("message", "Unknown error")
        raise RuntimeError(f"API error: {error_msg}")

    audio_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    pcm = base64.b64decode(audio_b64)

    # Save as WAV first (24kHz, 16-bit, mono)
    wav_path = output_path.replace(".mp3", ".wav")
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)

    # Convert to MP3 with ffmpeg
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", output_path],
        capture_output=True,
        timeout=30,
    )
    os.remove(wav_path)

    return os.path.getsize(output_path) / 1024


def main():
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not set. Run: export $(grep -v '^#' .env | grep -v '^$' | xargs)")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating narration for {len(SCENES)} scenes...")
    print(f"Voice: {VOICE_NAME} (Google Gemini TTS)")
    print(f"Model: {MODEL}\n")

    generated = 0
    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{text[:50]}\"", end="", flush=True)
        try:
            size = generate_scene_audio(text, output_path)
            print(f" -> {size:.1f}KB")
            generated += 1
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(1.0)  # Rate limiting

    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")])
    print(f"\nDone! {total}/{len(SCENES)} narration files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
