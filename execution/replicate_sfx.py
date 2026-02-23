#!/usr/bin/env python3
"""
Shared SFX generation via Replicate AudioGen (Meta's audio generation model).

Replaces ElevenLabs Sound Effects API — costs $0.012/run vs ~1,500 ElevenLabs credits/video.

Usage:
    from replicate_sfx import generate_sfx
    generate_sfx("cinematic whoosh sound", 2.5, "output/sfx_00.mp3")
"""

import os
import time
import requests
import replicate

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

MAX_RETRIES = 3
RETRY_WAIT = 12  # seconds — stay under 6 req/min rate limit


def generate_sfx(prompt, duration, output_path):
    """Generate a sound effect via Replicate AudioGen and save to disk.

    Args:
        prompt: Text description of the desired sound effect
        duration: Duration in seconds
        output_path: Where to save the file

    Returns:
        File size in KB
    """
    for attempt in range(MAX_RETRIES):
        try:
            output = replicate.run(
                "sepal/audiogen:154b3e5141493cb1b8cec976d9aa90f2b691137e39ad906d2421b74c2a8c52b8",
                input={
                    "prompt": prompt,
                    "duration": min(int(duration), 10),
                    "output_format": "wav",
                },
            )

            # output is a FileOutput URL — download it
            resp = requests.get(str(output), timeout=120)
            resp.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(resp.content)

            return len(resp.content) / 1024

        except Exception as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
                continue
            raise
