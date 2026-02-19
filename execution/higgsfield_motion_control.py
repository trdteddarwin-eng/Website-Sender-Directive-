#!/usr/bin/env python3
"""
KIE Kling Motion Control — Video Generation via kie.ai API

Submits a reference video and avatar image to KIE's Kling Motion Control
to generate a new video with the avatar replacing the original person.

Uses KIE REST API (docs: https://docs.kie.ai).

Part of the TikTok Avatar Pipeline:
  1. Download TikTok videos
  2. Filter for talking-head format
  3. Submit to KIE Kling Motion Control (this script)
  4. Post generated videos

Usage:
  python3 execution/higgsfield_motion_control.py \
    --video .tmp/tiktok_downloads/video123.mp4 \
    --avatar tiktok-avatar-pipeline/avatar.jpg \
    --output-dir .tmp/tiktok_generated/
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# KIE API Configuration
# ---------------------------------------------------------------------------

KIE_API_KEY = os.getenv("KIE_API_KEY")

KIE_API_BASE = "https://api.kie.ai"
KIE_UPLOAD_BASE = "https://kieai.redpandaai.co"

# Model: Kling 2.6 Motion Control
# Takes a reference image + motion video → generates avatar video
KLING_MOTION_CONTROL_MODEL = "kling-2.6/motion-control"


def _headers():
    """Auth headers for KIE API calls."""
    return {"Authorization": f"Bearer {KIE_API_KEY}"}


# ---------------------------------------------------------------------------
# File Upload
# ---------------------------------------------------------------------------

def _upload_file(file_path):
    """
    Upload a local file to KIE's file storage via stream upload.

    Returns the file URL on success, None on failure.
    Files are retained for 3 days.
    """
    url = f"{KIE_UPLOAD_BASE}/api/file-stream-upload"

    ext = os.path.splitext(file_path)[1].lower()
    basename = os.path.basename(file_path)

    # Determine upload path by file type
    if ext in (".mp4", ".mov", ".mkv"):
        upload_path = "videos"
    else:
        upload_path = "images"

    with open(file_path, "rb") as f:
        files = {
            "file": (basename, f),
            "uploadPath": (None, upload_path),
            "fileName": (None, basename),
        }
        resp = requests.post(url, headers=_headers(), files=files, timeout=120)

    if resp.status_code != 200:
        print(f"  [ERROR] Upload failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return None

    data = resp.json()
    if not data.get("success") and data.get("code") != 200:
        print(f"  [ERROR] Upload error: {data.get('msg', 'Unknown')}", file=sys.stderr)
        return None

    file_url = data.get("data", {}).get("fileUrl") or data.get("data", {}).get("downloadUrl")
    if not file_url:
        print(f"  [ERROR] No file URL in upload response: {json.dumps(data, indent=2)}", file=sys.stderr)
        return None

    return file_url


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def run_motion_control(video_path, avatar_path, output_dir=".tmp/tiktok_generated/",
                       timeout=600, poll_interval=10, duration=10, prompt=None):
    """
    End-to-end: upload files -> submit motion control -> poll -> download result.

    Args:
        video_path:    Path to the reference video (.mp4).
        avatar_path:   Path to the avatar image (.jpg/.png).
        output_dir:    Directory to save the generated video.
        timeout:       Max seconds to wait for generation (default 600 = 10min).
        poll_interval: Seconds between status checks.
        duration:      Unused (motion control duration = reference video duration).
        prompt:        Custom prompt for generation (default: "person talking to camera, natural movement").

    Returns:
        str path to the generated video on success, None on failure.
    """
    # ---- Pre-flight checks ------------------------------------------------
    if not KIE_API_KEY:
        print(
            "[ERROR] KIE_API_KEY not set. Add it to .env\n"
            "  Get yours at: https://kie.ai/api-key",
            file=sys.stderr,
        )
        return None

    if not os.path.isfile(video_path):
        print(f"[ERROR] Video file not found: {video_path}", file=sys.stderr)
        return None

    if not os.path.isfile(avatar_path):
        print(f"[ERROR] Avatar file not found: {avatar_path}", file=sys.stderr)
        return None

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("KIE Kling 2.6 Motion Control")
    print(f"  Video:  {video_path}")
    print(f"  Avatar: {avatar_path}")
    print(f"  Output: {output_dir}")
    print(f"  Model:  {KLING_MOTION_CONTROL_MODEL}")
    print("=" * 60)

    # ---- Step 1: Upload files ---------------------------------------------
    print("\n[1/4] Uploading avatar image...")
    avatar_url = _upload_file(avatar_path)
    if not avatar_url:
        return None
    print(f"  Avatar: {avatar_url}")

    print("\n[2/4] Uploading reference video...")
    video_url = _upload_file(video_path)
    if not video_url:
        return None
    print(f"  Video:  {video_url}")

    # ---- Step 2: Create task ----------------------------------------------
    print(f"\n[3/4] Submitting task ({KLING_MOTION_CONTROL_MODEL})...")
    generation_prompt = prompt or "person talking to camera, natural movement"
    task_body = {
        "model": KLING_MOTION_CONTROL_MODEL,
        "input": {
            "input_urls": [avatar_url],
            "video_urls": [video_url],
            "mode": "1080p",
            "character_orientation": "image",
        },
        "prompt": generation_prompt,
    }

    resp = requests.post(
        f"{KIE_API_BASE}/api/v1/jobs/createTask",
        headers={**_headers(), "Content-Type": "application/json"},
        json=task_body,
        timeout=60,
    )

    if resp.status_code != 200:
        print(f"[ERROR] Task creation failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        return None

    result = resp.json()
    if result.get("code") != 200:
        print(f"[ERROR] Task error: {result.get('msg', 'Unknown')}", file=sys.stderr)
        return None

    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        print(f"[ERROR] No taskId in response: {json.dumps(result, indent=2)}", file=sys.stderr)
        return None

    print(f"  Task ID: {task_id}")

    # ---- Step 3: Poll for completion --------------------------------------
    print(f"\n[4/4] Waiting for generation (timeout={timeout}s)...")
    start = time.time()

    while True:
        elapsed = int(time.time() - start)
        if elapsed > timeout:
            print(f"[ERROR] Timed out after {timeout}s", file=sys.stderr)
            return None

        # Adaptive polling: fast early, slow later
        if elapsed < 30:
            sleep_time = 3
        elif elapsed < 120:
            sleep_time = 5
        else:
            sleep_time = 15

        time.sleep(sleep_time)

        resp = requests.get(
            f"{KIE_API_BASE}/api/v1/jobs/recordInfo",
            headers=_headers(),
            params={"taskId": task_id},
            timeout=30,
        )

        if resp.status_code != 200:
            print(f"  [WARN] Status check failed ({resp.status_code}), retrying...", file=sys.stderr)
            continue

        status_data = resp.json()
        if status_data.get("code") != 200:
            print(f"  [WARN] Status error: {status_data.get('message', 'Unknown')}, retrying...", file=sys.stderr)
            continue

        task_info = status_data.get("data", {})
        state = task_info.get("state", "unknown")
        cost_time = task_info.get("costTime", 0)
        print(f"  {elapsed}s elapsed — state: {state} (processing: {cost_time}ms)")

        if state == "success":
            # Extract result URL from resultJson
            result_json_str = task_info.get("resultJson", "{}")
            try:
                result_json = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
            except json.JSONDecodeError:
                print(f"[ERROR] Could not parse resultJson: {result_json_str}", file=sys.stderr)
                return None

            output_url = _extract_output_url(result_json)
            if not output_url:
                print(f"[ERROR] No output URL in result: {json.dumps(result_json, indent=2)}", file=sys.stderr)
                return None

            # Get downloadable URL via KIE download endpoint
            download_url = _get_download_url(output_url)
            if not download_url:
                download_url = output_url  # fallback to raw URL

            return _download_output(download_url, output_dir)

        if state == "fail":
            fail_code = task_info.get("failCode", "")
            fail_msg = task_info.get("failMsg", "Unknown error")
            print(f"[ERROR] Generation failed: [{fail_code}] {fail_msg}", file=sys.stderr)
            return None


def _get_download_url(file_url):
    """Convert a KIE temp file URL to a downloadable URL (valid 20 minutes)."""
    resp = requests.post(
        f"{KIE_API_BASE}/api/v1/common/download-url",
        headers={**_headers(), "Content-Type": "application/json"},
        json={"url": file_url},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 200:
            return data.get("data")
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_output_url(result):
    """Extract the video output URL from KIE resultJson formats."""
    if isinstance(result, str):
        if result.startswith("http"):
            return result
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return None

    if isinstance(result, dict):
        # KIE motion control format: {"resultUrls": ["https://..."]}
        result_urls = result.get("resultUrls")
        if isinstance(result_urls, list) and result_urls:
            url = result_urls[0]
            if isinstance(url, str) and url.startswith("http"):
                return url

        # Common KIE patterns
        for key in ("video_url", "output_url", "result_url", "url", "download_url", "video"):
            val = result.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                return val

        # Nested under output/result/data/works
        for key in ("output", "result", "data", "works"):
            nested = result.get(key)
            if isinstance(nested, dict):
                for subkey in ("video", "url", "video_url", "download_url", "resource"):
                    val = nested.get(subkey)
                    if val and isinstance(val, str) and val.startswith("http"):
                        return val
            if isinstance(nested, list) and nested:
                item = nested[0]
                if isinstance(item, dict):
                    for subkey in ("video", "url", "video_url", "resource"):
                        val = item.get(subkey)
                        if val and isinstance(val, str) and val.startswith("http"):
                            return val
                elif isinstance(item, str) and item.startswith("http"):
                    return item

    return None


def _download_output(output_url, output_dir):
    """Download the generated video to output_dir."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"generated_{timestamp}.mp4")
    os.makedirs(output_dir, exist_ok=True)

    print(f"  Downloading result to {output_path}")
    try:
        resp = requests.get(output_url, stream=True, timeout=120)
        if resp.status_code >= 400:
            print(f"[ERROR] Download failed ({resp.status_code})", file=sys.stderr)
            return None

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(output_path)
        print(f"  Download complete: {output_path} ({file_size:,} bytes)")
        return output_path

    except Exception as e:
        print(f"[ERROR] Download failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="KIE Kling Motion Control — generate avatar videos"
    )
    parser.add_argument(
        "--video", required=True,
        help="Path to the reference video (.mp4)",
    )
    parser.add_argument(
        "--avatar", required=True,
        help="Path to the avatar image (.jpg/.png)",
    )
    parser.add_argument(
        "--output-dir", default=".tmp/tiktok_generated/",
        help="Directory to save generated videos (default: .tmp/tiktok_generated/)",
    )
    parser.add_argument(
        "--timeout", type=int, default=600,
        help="Max seconds to wait for generation (default: 600)",
    )
    parser.add_argument(
        "--poll-interval", type=int, default=10,
        help="Seconds between status checks (default: 10)",
    )
    parser.add_argument(
        "--duration", type=int, default=10,
        help="Video duration in seconds (unused for motion control, kept for API compat)",
    )
    parser.add_argument(
        "--prompt",
        help="Custom prompt for generation (default: 'person talking to camera, natural movement')",
    )

    args = parser.parse_args()

    result = run_motion_control(
        video_path=args.video,
        avatar_path=args.avatar,
        output_dir=args.output_dir,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        duration=args.duration,
        prompt=args.prompt,
    )

    if result:
        print(json.dumps({"status": "success", "output": result}))
        sys.exit(0)
    else:
        print(json.dumps({"status": "error", "output": None}))
        sys.exit(1)


if __name__ == "__main__":
    main()
