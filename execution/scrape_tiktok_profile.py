#!/usr/bin/env python3
"""
Scrape all videos from a TikTok profile using Apify's clockworks/tiktok-profile-scraper.
Downloads video files and saves metadata.

Usage:
  python3 execution/scrape_tiktok_profile.py --username "conversion.doc" --max-videos 30 --download --download-dir .tmp/tiktok_conversion_doc
"""

import os
import sys
import json
import argparse
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()


def scrape_profile(username: str, max_videos: int = 30) -> Optional[List[Dict[str, Any]]]:
    """
    Scrape videos from a TikTok profile using Apify clockworks/tiktok-profile-scraper.
    Returns list of video metadata dicts.
    """
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("Error: APIFY_API_TOKEN not found in .env", file=sys.stderr)
        return None

    client = ApifyClient(api_token)

    # Clean username (remove @ if present)
    username = username.lstrip("@")

    run_input = {
        "profiles": [username],
        "resultsPerPage": int(max_videos),
        "maxProfileItems": int(max_videos),
        "shouldDownloadVideos": False,  # We download ourselves for better control
    }

    print(f"Scraping @{username} profile (limit: {max_videos} videos)...")
    print(f"  Actor: clockworks/tiktok-profile-scraper")

    try:
        run = client.actor("clockworks/tiktok-profile-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"Error running actor: {e}", file=sys.stderr)
        return None

    if not run:
        print("Error: Actor run failed", file=sys.stderr)
        return None

    print(f"Scrape finished (dataset: {run['defaultDatasetId']}). Fetching results...")

    results = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"  Got {len(results)} videos")
    return results


def _extract_download_url(video: Dict[str, Any]) -> Optional[str]:
    """Extract best download URL from video metadata."""
    for key in ("videoUrl", "downloadAddr"):
        url = video.get(key)
        if url:
            return url

    video_obj = video.get("video", {})
    if isinstance(video_obj, dict):
        for key in ("downloadAddr", "playAddr"):
            url = video_obj.get(key)
            if url:
                return url

    return None


def _extract_video_id(video: Dict[str, Any]) -> str:
    """Extract video ID, falling back to hash."""
    for key in ("id", "videoId", "video_id"):
        vid = video.get(key)
        if vid:
            return str(vid)

    video_obj = video.get("video", {})
    if isinstance(video_obj, dict):
        vid = video_obj.get("id")
        if vid:
            return str(vid)

    web_url = video.get("webVideoUrl", "") or video.get("url", "")
    if web_url:
        return str(abs(hash(web_url)))

    return str(abs(hash(json.dumps(video, sort_keys=True, default=str))))


def _download_via_ytdlp(web_url: str, local_path: str) -> bool:
    """Download via yt-dlp. Returns True on success."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "-o", local_path, "--no-warnings", "-q", web_url],
            capture_output=True, text=True, timeout=120,
        )
        return result.returncode == 0 and os.path.exists(local_path)
    except Exception:
        return False


def _download_single(video: Dict, download_dir: str, headers: Dict) -> tuple:
    """Download a single video. Returns (video_dict, success, status)."""
    video_id = _extract_video_id(video)
    local_path = os.path.join(download_dir, f"{video_id}.mp4")

    if os.path.exists(local_path):
        return ({**video, "video_id": video_id, "local_path": local_path}, True, "cached")

    url = _extract_download_url(video)
    success = False

    if url:
        try:
            resp = requests.get(url, stream=True, headers=headers, timeout=60)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            success = True
        except Exception:
            if os.path.exists(local_path):
                os.remove(local_path)

    if not success:
        web_url = video.get("webVideoUrl") or video.get("url")
        if web_url:
            success = _download_via_ytdlp(web_url, local_path)

    if success and os.path.exists(local_path):
        return ({**video, "video_id": video_id, "local_path": local_path}, True, "downloaded")
    return (video, False, "failed")


def download_videos(video_list: List[Dict], download_dir: str, max_workers: int = 5) -> List[Dict]:
    """Download video files in parallel. Returns list of successful downloads."""
    if not video_list:
        print("No videos to download.")
        return []

    os.makedirs(download_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    }

    total = len(video_list)
    print(f"Downloading {total} videos to {download_dir}...")

    downloaded = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_download_single, v, download_dir, headers): i
            for i, v in enumerate(video_list)
        }
        for future in as_completed(futures):
            idx = futures[future] + 1
            try:
                result, success, status = future.result()
                vid = result.get("video_id", "?")
                if success:
                    downloaded.append(result)
                    print(f"  [{idx}/{total}] {vid}.mp4 — {status}")
                else:
                    print(f"  [{idx}/{total}] {vid} — failed", file=sys.stderr)
            except Exception as e:
                print(f"  [{idx}/{total}] error: {e}", file=sys.stderr)

    print(f"Downloaded {len(downloaded)}/{total} videos")
    return downloaded


def get_view_count(video: Dict) -> int:
    """Extract view count from video metadata."""
    for key in ("playCount", "plays", "views", "viewCount"):
        val = video.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

    stats = video.get("stats", {})
    if isinstance(stats, dict):
        val = stats.get("playCount") or stats.get("plays")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

    return 0


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok profile videos via Apify")
    parser.add_argument("--username", required=True, help="TikTok username (with or without @)")
    parser.add_argument("--max-videos", type=int, default=30, help="Max videos to scrape")
    parser.add_argument("--download", action="store_true", help="Download .mp4 files")
    parser.add_argument("--download-dir", default=".tmp/tiktok_profile", help="Download directory")

    args = parser.parse_args()

    # Step 1: Scrape profile
    results = scrape_profile(args.username, args.max_videos)
    if not results:
        print("No videos found or error occurred.")
        sys.exit(1)

    # Sort by views (highest first)
    results.sort(key=get_view_count, reverse=True)

    print(f"\nTop 5 by views:")
    for i, v in enumerate(results[:5]):
        views = get_view_count(v)
        desc = (v.get("text", "") or v.get("desc", "") or "")[:60]
        print(f"  {i+1}. {views:,} views — {desc}")

    # Step 2: Download if requested
    if args.download:
        results = download_videos(results, args.download_dir)

    # Step 3: Save metadata
    output_dir = args.download_dir if args.download else ".tmp"
    os.makedirs(output_dir, exist_ok=True)
    metadata_path = os.path.join(output_dir, "metadata.json")

    with open(metadata_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nMetadata saved to {metadata_path} ({len(results)} videos)")

    return results


if __name__ == "__main__":
    main()
