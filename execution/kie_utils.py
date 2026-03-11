#!/usr/bin/env python3
"""
Shared utilities for KIE API (ElevenLabs proxy).

Models:
  - elevenlabs/text-to-dialogue-v3 (TTS narration)
  - elevenlabs/sound-effect-v2 (SFX)

See: execution/kie_api_docs/text-to-dialogue-v3.md
     execution/kie_api_docs/sound-effect-v2.md
"""

import json
import os
import subprocess
import time

import requests

KIE_API_KEY = os.getenv("KIE_API_KEY", "")
API_BASE = "https://api.kie.ai"


def create_and_poll(model, inp, max_attempts=40, poll_interval=3):
    """Create a KIE task and poll until completion. Returns list of result URLs or None."""
    headers = {
        "Authorization": "Bearer %s" % KIE_API_KEY,
        "Content-Type": "application/json",
    }
    r = requests.post(
        "%s/api/v1/jobs/createTask" % API_BASE,
        headers=headers,
        json={"model": model, "input": inp},
        timeout=30,
    )
    if r.status_code != 200 or r.json().get("code") != 200:
        print("  [KIE] createTask failed: %s" % r.text[:200])
        return None

    task_id = r.json()["data"]["taskId"]
    poll_headers = {"Authorization": "Bearer %s" % KIE_API_KEY}

    for attempt in range(max_attempts):
        time.sleep(poll_interval)
        r2 = requests.get(
            "%s/api/v1/jobs/recordInfo" % API_BASE,
            params={"taskId": task_id},
            headers=poll_headers,
            timeout=15,
        )
        data = r2.json().get("data", {})
        state = data.get("state", "")
        if state == "success":
            result = json.loads(data.get("resultJson", "{}"))
            return result.get("resultUrls", [])
        if state in ("failed", "error", "fail"):
            fail_msg = data.get("failMsg", "unknown")
            print("  [KIE] Task failed: %s" % fail_msg)
            return None

    print("  [KIE] Timeout after %d attempts" % max_attempts)
    return None


def download(url, path):
    """Download a file from URL. Returns True if file is valid (>500 bytes)."""
    r = requests.get(url, timeout=60)
    with open(path, "wb") as f:
        f.write(r.content)
    return os.path.getsize(path) > 500


def get_duration(path):
    """Get audio duration in seconds using ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 3.0


def generate_narration(text, output_path):
    """Generate TTS narration via KIE (elevenlabs/text-to-dialogue-v3). Returns duration in seconds."""
    urls = create_and_poll(
        "elevenlabs/text-to-dialogue-v3",
        {"dialogue": [{"text": text, "voice": "Liam"}], "stability": 0.5, "language_code": "en"},
    )
    if urls and download(urls[0], output_path):
        return get_duration(output_path)
    return None


def generate_sfx(prompt, duration_seconds, output_path):
    """Generate SFX via KIE (elevenlabs/sound-effect-v2). Returns file size in KB."""
    urls = create_and_poll(
        "elevenlabs/sound-effect-v2",
        {"text": prompt, "duration_seconds": duration_seconds},
    )
    if urls and download(urls[0], output_path):
        return os.path.getsize(output_path) / 1024
    return None
