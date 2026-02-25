#!/usr/bin/env python3
"""
Generate background music for the TikTok recreation using Google Lyria RealTime.

Usage:
  python execution/generate_background_music.py

Output:
  tiktok-recreation/public/background-music.mp3
"""

import asyncio
import os
import struct
import subprocess
import sys
import tempfile

from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OUTPUT_PATH = "tiktok-recreation/public/background-music.mp3"
TARGET_DURATION_S = 42  # slightly longer than 39.2s video to avoid cutoff

# Audio format from Lyria RealTime: 48kHz, 16-bit PCM, stereo
SAMPLE_RATE = 48000
CHANNELS = 2
BYTES_PER_SAMPLE = 2
BYTES_PER_SECOND = SAMPLE_RATE * CHANNELS * BYTES_PER_SAMPLE
TARGET_BYTES = TARGET_DURATION_S * BYTES_PER_SECOND


async def generate_music():
    """Generate background music via Lyria RealTime WebSocket."""
    client = genai.Client(
        api_key=GOOGLE_API_KEY,
        http_options={"api_version": "v1alpha"},
    )

    pcm_data = bytearray()
    print(f"Connecting to Lyria RealTime...")

    async with client.aio.live.music.connect(model="models/lyria-realtime-exp") as session:
        # Set music style - cinematic, motivational background music
        await session.set_weighted_prompts(
            prompts=[
                types.WeightedPrompt(
                    text="cinematic motivational ambient background music, modern, inspiring, corporate video",
                    weight=1.0,
                ),
                types.WeightedPrompt(
                    text="soft electronic beats, warm pads, uplifting atmosphere",
                    weight=0.6,
                ),
            ]
        )

        # Configure generation
        await session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(
                bpm=95,
                temperature=1.0,
                guidance=4.0,
                brightness=0.6,
                density=0.4,
                mute_drums=False,
                mute_bass=False,
            )
        )

        # Start playback and collect audio chunks
        await session.play()
        print(f"Generating {TARGET_DURATION_S}s of background music...")

        async for message in session.receive():
            if message.server_content and message.server_content.audio_chunks:
                chunk = message.server_content.audio_chunks[0].data
                pcm_data.extend(chunk)

                current_s = len(pcm_data) / BYTES_PER_SECOND
                if int(current_s) % 5 == 0 and int(current_s) > 0:
                    pct = min(100, int(current_s / TARGET_DURATION_S * 100))
                    print(f"  {current_s:.0f}s / {TARGET_DURATION_S}s ({pct}%)", flush=True)

                if len(pcm_data) >= TARGET_BYTES:
                    print(f"  Reached target duration ({current_s:.1f}s)")
                    break

    return bytes(pcm_data)


def pcm_to_mp3(pcm_data, output_path):
    """Convert raw PCM audio to MP3 using ffmpeg."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as tmp:
        tmp.write(pcm_data)
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "s16le",          # 16-bit signed little-endian PCM
            "-ar", str(SAMPLE_RATE), # 48kHz
            "-ac", str(CHANNELS),    # stereo
            "-i", tmp_path,
            "-codec:a", "libmp3lame",
            "-q:a", "2",            # high quality VBR
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            sys.exit(1)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"  Saved: {output_path} ({size_kb:.0f}KB)")
    finally:
        os.unlink(tmp_path)


def main():
    print("Generating background music with Google Lyria RealTime...")
    pcm_data = asyncio.run(generate_music())

    duration_s = len(pcm_data) / BYTES_PER_SECOND
    print(f"\nCollected {duration_s:.1f}s of raw PCM audio ({len(pcm_data)} bytes)")

    print("Converting to MP3...")
    pcm_to_mp3(pcm_data, OUTPUT_PATH)

    print("\nDone! Background music saved.")


if __name__ == "__main__":
    main()
