#!/usr/bin/env python3
"""
UGC Video Generation Pipeline — Kling 3.0 via KIE API

Generates multi-scene UGC ads from a single avatar image.
Chains scenes by extracting the last frame of each video as input for the next.

Usage:
  python3 execution/generate_ugc_video.py \
    --avatar ugc-miyou/assets/avatar_1080.jpg \
    --product ugc-miyou/assets/product_1080.jpg \
    --output-dir ugc-miyou/output/ \
    --scenes ugc-miyou/scenes.json

Requires: KIE_API_KEY, ELEVENLABS_API_KEY in .env
"""

import os
import sys
import json
import argparse
import time
import subprocess
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API Config
# ---------------------------------------------------------------------------

KIE_API_KEY = os.getenv("KIE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

KIE_API_BASE = "https://api.kie.ai"
KIE_UPLOAD_BASE = "https://kieai.redpandaai.co"

# Kling 3.0 image-to-video
KLING_MODEL = "kling-3.0/video"

# ElevenLabs voice defaults
DEFAULT_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"  # Liam — young, energetic, social media creator
DEFAULT_VOICE_MODEL = "eleven_multilingual_v2"


# ---------------------------------------------------------------------------
# KIE Auth
# ---------------------------------------------------------------------------

def _kie_headers():
    return {"Authorization": f"Bearer {KIE_API_KEY}"}


# ---------------------------------------------------------------------------
# KIE File Upload
# ---------------------------------------------------------------------------

def upload_to_kie(file_path: str) -> str:
    """Upload a local file to KIE storage. Returns the file URL."""
    url = f"{KIE_UPLOAD_BASE}/api/file-stream-upload"
    ext = os.path.splitext(file_path)[1].lower()
    basename = os.path.basename(file_path)
    upload_path = "videos" if ext in (".mp4", ".mov", ".mkv") else "images"

    print(f"  Uploading {basename}...")
    with open(file_path, "rb") as f:
        files = {
            "file": (basename, f),
            "uploadPath": (None, upload_path),
            "fileName": (None, basename),
        }
        resp = requests.post(url, headers=_kie_headers(), files=files, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"Upload failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    if not data.get("success") and data.get("code") != 200:
        raise RuntimeError(f"Upload error: {data.get('msg', 'Unknown')}")

    file_url = data.get("data", {}).get("fileUrl") or data.get("data", {}).get("downloadUrl")
    if not file_url:
        raise RuntimeError(f"No file URL in upload response: {json.dumps(data)}")

    print(f"  Uploaded: {file_url}")
    return file_url


# ---------------------------------------------------------------------------
# KIE Kling 3.0 Image-to-Video
# ---------------------------------------------------------------------------

def submit_scene(image_url: str, prompt: str, duration: int = 10,
                 aspect_ratio: str = "9:16", mode: str = "pro",
                 negative_prompt: Optional[str] = None,
                 elements: Optional[list] = None) -> str:
    """
    Submit an image-to-video task to KIE Kling 3.0.
    Returns the taskId for polling.
    """
    task_body = {
        "model": KLING_MODEL,
        "input": {
            "prompt": prompt,
            "image_urls": [image_url],
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "duration": str(duration),
            "multi_shots": False,
            "multi_prompt": [],
            "sound": False,
        },
    }

    if negative_prompt:
        task_body["input"]["negative_prompt"] = negative_prompt

    if elements:
        task_body["input"]["kling_elements"] = elements

    resp = requests.post(
        f"{KIE_API_BASE}/api/v1/jobs/createTask",
        headers={**_kie_headers(), "Content-Type": "application/json"},
        json=task_body,
        timeout=60,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Task creation failed ({resp.status_code}): {resp.text}")

    result = resp.json()
    if result.get("code") != 200:
        raise RuntimeError(f"Task error: {result.get('msg', 'Unknown')} — {json.dumps(result)}")

    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"No taskId in response: {json.dumps(result)}")

    print(f"  Task submitted: {task_id}")
    return task_id


def poll_scene(task_id: str, timeout: int = 600) -> str:
    """
    Poll KIE for task completion.
    Returns the output video URL on success.
    """
    start = time.time()

    while True:
        elapsed = int(time.time() - start)
        if elapsed > timeout:
            raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

        # Adaptive polling: fast early, slow later
        if elapsed < 30:
            wait = 3
        elif elapsed < 120:
            wait = 5
        else:
            wait = 15

        time.sleep(wait)

        resp = requests.get(
            f"{KIE_API_BASE}/api/v1/jobs/recordInfo",
            headers=_kie_headers(),
            params={"taskId": task_id},
            timeout=30,
        )

        if resp.status_code != 200:
            print(f"  [WARN] Status check failed ({resp.status_code}), retrying...")
            continue

        data = resp.json()
        if data.get("code") != 200:
            print(f"  [WARN] Status error: {data.get('message', 'Unknown')}, retrying...")
            continue

        task_info = data.get("data", {})
        state = task_info.get("state", "unknown")
        cost_time = task_info.get("costTime", 0)
        print(f"  {elapsed}s elapsed — state: {state} (processing: {cost_time}ms)")

        if state == "success":
            result_json_str = task_info.get("resultJson", "{}")
            try:
                result_json = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
            except json.JSONDecodeError:
                raise RuntimeError(f"Could not parse resultJson: {result_json_str}")

            output_url = _extract_output_url(result_json)
            if not output_url:
                raise RuntimeError(f"No output URL in result: {json.dumps(result_json, indent=2)}")

            # Get downloadable URL
            download_url = _get_download_url(output_url)
            return download_url or output_url

        if state == "fail":
            fail_code = task_info.get("failCode", "")
            fail_msg = task_info.get("failMsg", "Unknown error")
            raise RuntimeError(f"Generation failed: [{fail_code}] {fail_msg}")


def _extract_output_url(result) -> Optional[str]:
    """Extract the video output URL from KIE resultJson."""
    if isinstance(result, str):
        if result.startswith("http"):
            return result
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return None

    if isinstance(result, dict):
        # KIE format: {"resultUrls": ["https://..."]}
        result_urls = result.get("resultUrls")
        if isinstance(result_urls, list) and result_urls:
            url = result_urls[0]
            if isinstance(url, str) and url.startswith("http"):
                return url

        # Fallback patterns
        for key in ("video_url", "output_url", "result_url", "url", "download_url", "video"):
            val = result.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                return val

        # Nested
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


def _get_download_url(file_url: str) -> Optional[str]:
    """Convert KIE temp URL to a downloadable URL (valid 20 min)."""
    resp = requests.post(
        f"{KIE_API_BASE}/api/v1/common/download-url",
        headers={**_kie_headers(), "Content-Type": "application/json"},
        json={"url": file_url},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 200:
            return data.get("data")
    return None


def download_video(url: str, output_path: str) -> str:
    """Download video from URL to local path."""
    resp = requests.get(url, stream=True, timeout=180)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    size = os.path.getsize(output_path)
    print(f"  Downloaded: {output_path} ({size:,} bytes)")
    return output_path


# ---------------------------------------------------------------------------
# Frame Extraction (ffmpeg)
# ---------------------------------------------------------------------------

def extract_last_frame(video_path: str, output_path: str) -> str:
    """Extract the last frame of a video as a JPEG image."""
    subprocess.run(
        ["ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path,
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True, timeout=30
    )
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to extract last frame from {video_path}")
    print(f"  Last frame: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# ElevenLabs Voiceover
# ---------------------------------------------------------------------------

def generate_voiceover(text: str, output_path: str,
                       voice_id: str = DEFAULT_VOICE_ID) -> str:
    """Generate voiceover audio using ElevenLabs TTS."""
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": DEFAULT_VOICE_MODEL,
            "voice_settings": {
                "stability": 0.35,
                "similarity_boost": 0.80,
                "style": 0.4,
            }
        },
        timeout=60
    )
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    print(f"  Voiceover: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Video Stitching (ffmpeg)
# ---------------------------------------------------------------------------

def stitch_final_video(scene_videos: list, voiceover_path: str,
                       output_path: str) -> str:
    """Concat all scene videos, overlay voiceover audio, output final video."""
    output_dir = os.path.dirname(output_path)
    concat_file = os.path.join(output_dir, "_concat_list.txt")
    concat_video = os.path.join(output_dir, "_concat_raw.mp4")

    # Create concat list
    with open(concat_file, "w") as f:
        for vp in scene_videos:
            f.write(f"file '{os.path.abspath(vp)}'\n")

    # Concat videos (re-encode for consistent codec)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c:v", "libx264", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", "30",
         "-an", concat_video],
        capture_output=True, timeout=300
    )
    if not os.path.exists(concat_video):
        raise RuntimeError("Failed to concatenate scene videos")

    # Overlay voiceover
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", concat_video, "-i", voiceover_path,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-map", "0:v:0", "-map", "1:a:0",
         "-shortest", output_path],
        capture_output=True, timeout=300
    )

    # Cleanup
    for f in [concat_file, concat_video]:
        if os.path.exists(f):
            os.remove(f)

    if not os.path.exists(output_path):
        raise RuntimeError("Failed to create final video")

    size = os.path.getsize(output_path)
    print(f"\n  FINAL VIDEO: {output_path} ({size:,} bytes)")
    return output_path


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def load_scenes(scenes_path: str) -> list:
    """Load scene definitions from JSON file."""
    with open(scenes_path) as f:
        return json.load(f)


def run_pipeline(avatar_path: str, product_path: str, output_dir: str,
                 scenes: list, mode: str = "1080p",
                 voice_id: str = DEFAULT_VOICE_ID):
    """
    Full UGC generation pipeline:
    1. Upload images to KIE
    2. Generate each scene (chaining last frames)
    3. Generate voiceover
    4. Stitch final video
    """
    os.makedirs(output_dir, exist_ok=True)
    scenes_dir = os.path.join(output_dir, "scenes")
    os.makedirs(scenes_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("LA BELLE MIYOU — UGC VIDEO GENERATOR")
    print(f"  Avatar:  {avatar_path}")
    print(f"  Product: {product_path}")
    print(f"  Model:   {KLING_MODEL}")
    print(f"  Mode:    {mode}")
    print(f"  Scenes:  {len(scenes)}")
    print(f"  Output:  {output_dir}")
    print("=" * 60)

    # ---- Step 1: Upload images ----
    print("\n[1/4] Uploading images to KIE...")
    avatar_url = upload_to_kie(avatar_path)

    # ---- Step 2: Generate scenes ----
    print(f"\n[2/4] Generating {len(scenes)} scenes...")
    scene_videos = []
    current_image_url = avatar_url

    for i, scene in enumerate(scenes):
        scene_name = scene.get("name", f"scene_{i}")
        prompt = scene["prompt"]
        duration = scene.get("duration", 10)

        print(f"\n{'='*40}")
        print(f"Scene {i+1}/{len(scenes)}: {scene_name}")
        print(f"{'='*40}")
        print(f"  Duration: {duration}s")
        print(f"  Input: {'avatar (original)' if i == 0 else 'last frame of prev scene'}")
        print(f"  Prompt: {prompt[:100]}...")

        # Per-scene mode override (falls back to global CLI mode)
        scene_mode = scene.get("mode", mode)

        # Submit job
        task_id = submit_scene(
            image_url=current_image_url,
            prompt=prompt,
            duration=duration,
            mode=scene_mode,
            negative_prompt="blur, distort, low quality, deformed face, extra fingers, watermark, text overlay, unnatural movement",
        )

        # Poll for result
        video_url = poll_scene(task_id, timeout=600)

        # Download video
        scene_video_path = os.path.join(scenes_dir, f"{i:02d}_{scene_name}.mp4")
        download_video(video_url, scene_video_path)
        scene_videos.append(scene_video_path)

        # Extract last frame for next scene (if not the last scene)
        if i < len(scenes) - 1:
            last_frame_path = os.path.join(scenes_dir, f"{i:02d}_{scene_name}_lastframe.jpg")
            extract_last_frame(scene_video_path, last_frame_path)
            current_image_url = upload_to_kie(last_frame_path)

        print(f"  Scene {i+1} complete!")

    if not scene_videos:
        print("\n[ERROR] No scenes were generated successfully.")
        sys.exit(1)

    # ---- Step 3: Generate voiceover ----
    print(f"\n[3/4] Generating voiceover...")
    full_script = " ... ".join(
        scene.get("voiceover", "") for scene in scenes if scene.get("voiceover")
    )
    voiceover_path = os.path.join(output_dir, "voiceover.mp3")
    generate_voiceover(full_script, voiceover_path, voice_id=voice_id)

    # ---- Step 4: Stitch final video ----
    print(f"\n[4/4] Stitching final video...")
    final_path = os.path.join(output_dir, f"ugc_miyou_{timestamp}.mp4")
    stitch_final_video(scene_videos, voiceover_path, final_path)

    print("\n" + "=" * 60)
    print("UGC VIDEO GENERATION COMPLETE")
    print(f"  Final: {final_path}")
    print(f"  Scenes generated: {len(scene_videos)}/{len(scenes)}")
    print("=" * 60)

    return final_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="La Belle Miyou — UGC Video Generator (Kling 3.0 via KIE)"
    )
    parser.add_argument("--avatar", required=True, help="Path to avatar image")
    parser.add_argument("--product", required=True, help="Path to product image")
    parser.add_argument("--output-dir", default="ugc-miyou/output/",
                        help="Output directory")
    parser.add_argument("--scenes", default="ugc-miyou/scenes.json",
                        help="Path to scenes JSON file")
    parser.add_argument("--mode", choices=["pro", "std"], default="pro",
                        help="Video quality: pro (1080p) or std (720p)")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID,
                        help="ElevenLabs voice ID")
    parser.add_argument("--scene-index", type=int, default=None,
                        help="Generate only a single scene by index (0-based) for testing")

    args = parser.parse_args()

    # Validate
    if not KIE_API_KEY:
        print("[ERROR] KIE_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    if not ELEVENLABS_API_KEY:
        print("[ERROR] ELEVENLABS_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.avatar):
        print(f"[ERROR] Avatar not found: {args.avatar}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.product):
        print(f"[ERROR] Product image not found: {args.product}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.scenes):
        print(f"[ERROR] Scenes file not found: {args.scenes}", file=sys.stderr)
        sys.exit(1)

    scenes = load_scenes(args.scenes)

    # Single scene test mode
    if args.scene_index is not None:
        if args.scene_index >= len(scenes):
            print(f"[ERROR] Scene index {args.scene_index} out of range (0-{len(scenes)-1})")
            sys.exit(1)
        scenes = [scenes[args.scene_index]]
        print(f"[TEST MODE] Generating only scene {args.scene_index}")

    result = run_pipeline(
        avatar_path=args.avatar,
        product_path=args.product,
        output_dir=args.output_dir,
        scenes=scenes,
        mode=args.mode,
        voice_id=args.voice_id,
    )

    if result:
        print(json.dumps({"status": "success", "output": result}))
    else:
        print(json.dumps({"status": "error"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
