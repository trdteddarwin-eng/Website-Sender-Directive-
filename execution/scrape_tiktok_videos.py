#!/usr/bin/env python3
"""
Scrape TikTok videos by keyword using Apify's clockworks/tiktok-scraper actor.
Optionally download the video files to disk.
"""

import os
import sys
import json
import argparse
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables
load_dotenv()


def scrape_videos(query, max_videos=20):
    """
    Run the Apify actor to search TikTok for videos matching a keyword.
    Returns a list of video metadata dicts or None on failure.
    """
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("Error: APIFY_API_TOKEN not found in .env", file=sys.stderr)
        return None

    client = ApifyClient(api_token)

    # Prepare the actor input for clockworks/tiktok-scraper
    run_input = {
        "searchQueries": [query],
        "resultsPerPage": int(max_videos),
        "maxItems": int(max_videos),
        "searchSection": "/video",
    }

    print(f"Starting TikTok video scrape for '{query}' (Limit: {max_videos})...")
    print(f"Debug: run_input = {json.dumps(run_input, indent=2)}")

    try:
        # Run the actor and wait for it to finish
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"Error running actor: {e}", file=sys.stderr)
        return None

    if not run:
        print("Error: Actor run failed to start", file=sys.stderr)
        return None

    print(f"Scrape finished. Fetching results from dataset {run['defaultDatasetId']}...")

    # Fetch results from the actor's default dataset
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    return results


def _extract_download_url(video):
    """
    Extract the best available download URL from a video metadata dict.
    TikTok scraper results vary in structure, so we check multiple fields.
    Returns the URL string or None.
    """
    # Direct top-level fields
    for key in ("videoUrl", "downloadAddr"):
        url = video.get(key)
        if url:
            return url

    # Nested under 'video' object
    video_obj = video.get("video", {})
    if isinstance(video_obj, dict):
        for key in ("downloadAddr", "playAddr"):
            url = video_obj.get(key)
            if url:
                return url

    return None


def _extract_video_id(video):
    """
    Extract a usable video ID from a video metadata dict.
    Falls back to hash of the URL if no ID field is found.
    """
    for key in ("id", "videoId", "video_id"):
        vid = video.get(key)
        if vid:
            return str(vid)

    # Try nested
    video_obj = video.get("video", {})
    if isinstance(video_obj, dict):
        vid = video_obj.get("id")
        if vid:
            return str(vid)

    # Fallback: use hash of the webVideoUrl or any URL
    web_url = video.get("webVideoUrl", "") or video.get("url", "")
    if web_url:
        return str(abs(hash(web_url)))

    return str(abs(hash(json.dumps(video, sort_keys=True, default=str))))


def _download_via_ytdlp(web_url, local_path):
    """Download a TikTok video using yt-dlp. Returns True on success."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "-o", local_path, "--no-warnings", "-q", web_url],
            capture_output=True, text=True, timeout=120,
        )
        return result.returncode == 0 and os.path.exists(local_path)
    except Exception:
        return False


def _download_single(video, download_dir, headers):
    """
    Download a single video. Used by ThreadPoolExecutor.
    Returns (video_dict_with_local_path, success_bool).
    """
    video_id = _extract_video_id(video)
    filename = f"{video_id}.mp4"
    local_path = os.path.join(download_dir, filename)

    # Skip if already downloaded
    if os.path.exists(local_path):
        return ({**video, "video_id": video_id, "local_path": local_path}, True, "cached")

    # Try direct URL first
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

    # Fall back to yt-dlp via webVideoUrl
    if not success:
        web_url = video.get("webVideoUrl") or video.get("url")
        if web_url:
            success = _download_via_ytdlp(web_url, local_path)

    if success and os.path.exists(local_path):
        return ({**video, "video_id": video_id, "local_path": local_path}, True, "downloaded")
    return (video, False, "failed")


def download_videos(video_list, download_dir=".tmp/tiktok_downloads", max_workers=5):
    """
    Download .mp4 files for each video in video_list (parallel, 5 workers).
    Tries direct URL first, then falls back to yt-dlp via webVideoUrl.
    Returns a list of dicts with {video_id, local_path, ...metadata} for successful downloads.
    Skips files that already exist on disk. Continues on failure.
    """
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
    print(f"Downloading {total} videos with {max_workers} parallel workers...")

    downloaded = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_download_single, video, download_dir, headers): i
            for i, video in enumerate(video_list)
        }
        for future in as_completed(futures):
            idx = futures[future] + 1
            try:
                result, success, status = future.result()
                video_id = result.get("video_id", _extract_video_id(result))
                if success:
                    downloaded.append(result)
                    print(f"  [{idx}/{total}] {video_id}.mp4 — {status}")
                else:
                    print(f"  [{idx}/{total}] {video_id} — failed", file=sys.stderr)
            except Exception as e:
                print(f"  [{idx}/{total}] error: {e}", file=sys.stderr)

    print(f"Downloaded {len(downloaded)}/{total} videos to {download_dir}")
    return downloaded


def save_results(results, prefix="tiktok_videos"):
    """
    Save results to a JSON file in .tmp/.
    Returns the filepath or None if no results.
    """
    if not results:
        print("No results to save.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = ".tmp"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/{prefix}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to {filename}")
    return filename


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok videos by keyword using Apify")
    parser.add_argument("--query", required=True, help="Search keyword (e.g., 'viral serum')")
    parser.add_argument("--max_videos", type=int, default=20, help="Maximum number of videos to fetch")
    parser.add_argument("--download", action="store_true", help="Download the actual .mp4 video files")
    parser.add_argument("--download_dir", default=".tmp/tiktok_downloads", help="Directory to save downloaded videos")
    parser.add_argument("--output_prefix", default="tiktok_videos", help="Prefix for the metadata JSON output file")

    args = parser.parse_args()

    # Step 1: Scrape video metadata
    results = scrape_videos(args.query, args.max_videos)

    if not results:
        print("No videos found or error occurred.")
        sys.exit(1)

    print(f"Found {len(results)} videos.")

    # Step 2: Optionally download video files
    if args.download:
        results = download_videos(results, args.download_dir)

    # Step 3: Save results
    save_results(results, prefix=args.output_prefix)


if __name__ == "__main__":
    main()
