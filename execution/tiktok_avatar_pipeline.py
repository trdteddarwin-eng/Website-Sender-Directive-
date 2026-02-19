#!/usr/bin/env python3
"""
TikTok Avatar Pipeline — End-to-end orchestrator.

Chains together 4 stages:
  1. scrape_tiktok_products  — find trending TikTok Shop products
  2. scrape_tiktok_videos    — scrape & download videos for a keyword
  3. filter_talking_head     — score/filter for talking-head content
  4. higgsfield_motion_control — generate avatar video via motion control

Three entry modes:
  --category    Full auto (product discovery -> scrape -> filter -> generate)
  --keyword     Skip product discovery, scrape videos directly
  --videos-dir  Skip scraping, filter existing videos -> generate
"""

import os
import sys
import json
import argparse
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Sibling-script imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape_tiktok_products import scrape_products, save_results as save_products
from scrape_tiktok_videos import scrape_videos, download_videos, save_results as save_videos
from filter_talking_head import filter_videos
from higgsfield_motion_control import run_motion_control
from create_reference_image import create_reference_image
from segment_and_generate import generate_full_video


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_search_keyword(product):
    """Build a TikTok search keyword from a product dict."""
    name = (
        product.get("title")
        or product.get("name")
        or product.get("productName", "")
    )
    if name:
        return f"{name} TikTok Shop"
    return "trending product TikTok Shop"


def save_pipeline_summary(results, output_dir):
    """Persist a timestamped JSON summary of the pipeline run."""
    os.makedirs(".tmp", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(".tmp", f"pipeline_results_{timestamp}.json")
    payload = {
        "timestamp": datetime.now().isoformat(),
        "output_dir": output_dir,
        "generated_count": len(results) if results else 0,
        "results": results or [],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSummary saved to {path}")
    return path


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args):
    """Execute the pipeline according to the selected entry mode."""

    # Validate avatar(s) exist
    if not os.path.isfile(args.avatar):
        print(f"Error: Avatar image not found at {args.avatar}", file=sys.stderr)
        sys.exit(1)

    # Validate gendered avatars if provided
    if args.avatar_male and not os.path.isfile(args.avatar_male):
        print(f"Error: Male avatar not found at {args.avatar_male}", file=sys.stderr)
        sys.exit(1)
    if args.avatar_female and not os.path.isfile(args.avatar_female):
        print(f"Error: Female avatar not found at {args.avatar_female}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # STEP 1: Get search keyword
    # ------------------------------------------------------------------
    if args.category:
        print("=== Step 1: Finding trending products ===")
        products = scrape_products(args.category, args.max_products)
        if not products:
            print("No products found", file=sys.stderr)
            return None
        save_products(products)
        # Pick the top product by sales/engagement and build a search keyword
        keyword = build_search_keyword(products[0])
        print(f"Selected product keyword: {keyword}")

    elif args.keyword:
        print("=== Step 1: Using provided keyword ===")
        keyword = args.keyword

    elif args.videos_dir:
        keyword = None  # skip to step 3

    else:
        print("Error: Provide --category, --keyword, or --videos-dir", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # STEP 2: Scrape and download videos (skip if --videos-dir)
    # ------------------------------------------------------------------
    scrape_metadata = None
    if keyword:
        print(f"\n=== Step 2: Scraping TikTok videos for '{keyword}' ===")
        videos = scrape_videos(keyword, args.max_videos)
        if not videos:
            print("No videos found", file=sys.stderr)
            return None
        save_videos(videos)
        scrape_metadata = videos  # Keep for engagement ranking
        downloaded = download_videos(videos)
        videos_dir = ".tmp/tiktok_downloads"
        print(f"Downloaded {len(downloaded) if downloaded else 0} videos to {videos_dir}")
    else:
        print("\n=== Step 2: Using existing videos ===")
        videos_dir = args.videos_dir

    # ------------------------------------------------------------------
    # STEP 3: Filter for talking heads (parallel + engagement ranking)
    # ------------------------------------------------------------------
    print(f"\n=== Step 3: Filtering for talking head videos (30-60s, parallel) ===")
    candidates = filter_videos(
        videos_dir, top_n=args.top_candidates, min_score=args.min_score,
        scrape_metadata=scrape_metadata,
    )
    if not candidates:
        print("No videos passed the talking head filter", file=sys.stderr)
        return None

    print(f"\nTop {len(candidates)} candidates:")
    for i, c in enumerate(candidates):
        rank = c.get("final_rank", c["composite_score"])
        print(f"  {i+1}. {os.path.basename(c['video_path'])} — score: {c['composite_score']:.0f}, rank: {rank:.3f}")

    if args.skip_generate:
        print("\n--skip-generate set, stopping here.")
        return candidates

    # ------------------------------------------------------------------
    # STEP 4: Generate full-length avatar videos (segment-based)
    # ------------------------------------------------------------------
    print(f"\n=== Step 4: Generating {args.generate_count} full-length avatar video(s) ===")
    print(f"  Method: Split → InsightFace swap → Kling 3.0 Pro (duration=10s) → Stitch + Audio")
    os.makedirs(args.output_dir, exist_ok=True)
    results = []
    for i, candidate in enumerate(candidates[: args.generate_count]):
        src = candidate["video_path"]
        print(f"\n--- Video {i+1}/{args.generate_count}: {os.path.basename(src)} ---")

        output = generate_full_video(
            source_video_path=src,
            avatar_path=args.avatar,
            output_dir=args.output_dir,
            segment_duration=10,
            avatar_male_path=args.avatar_male,
            avatar_female_path=args.avatar_female,
            enable_analysis=args.enable_analysis,
        )

        if output:
            results.append({
                "source": src,
                "generated": output,
                "score": candidate["composite_score"],
                "final_rank": candidate.get("final_rank"),
            })
            print(f"  Full video generated: {output}")
        else:
            print(f"  Generation failed for {src}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n=== Pipeline Complete ===")
    print(f"Generated {len(results)}/{args.generate_count} full-length videos")
    for r in results:
        print(f"  {r['generated']} (source score: {r['score']:.0f})")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TikTok Avatar Pipeline — find trending videos, filter, and generate avatar content.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full auto — discover products, scrape, filter, generate
  python3 execution/tiktok_avatar_pipeline.py \\
      --avatar tiktok-avatar-pipeline/avatar.jpg \\
      --category beauty --generate-count 1

  # From keyword — skip product discovery
  python3 execution/tiktok_avatar_pipeline.py \\
      --avatar tiktok-avatar-pipeline/avatar.jpg \\
      --keyword "viral beauty serum TikTok Shop"

  # From existing videos — skip scraping entirely
  python3 execution/tiktok_avatar_pipeline.py \\
      --avatar tiktok-avatar-pipeline/avatar.jpg \\
      --videos-dir .tmp/tiktok_downloads/
        """,
    )

    # Required
    parser.add_argument(
        "--avatar", required=True,
        help="Path to avatar image (e.g., tiktok-avatar-pipeline/avatar.jpg)",
    )

    # Entry-mode arguments (mutually informative, not enforced exclusive)
    parser.add_argument(
        "--category",
        help="TikTok Shop category for product discovery (mode 1: full auto)",
    )
    parser.add_argument(
        "--keyword",
        help="Direct search keyword, skips product discovery (mode 2)",
    )
    parser.add_argument(
        "--videos-dir",
        help="Path to already-downloaded videos, skips scraping (mode 3)",
    )

    # Tuning knobs
    parser.add_argument(
        "--max-products", type=int, default=5,
        help="Max products to scrape in category mode (default: 5)",
    )
    parser.add_argument(
        "--max-videos", type=int, default=20,
        help="Max videos to scrape per keyword (default: 20)",
    )
    parser.add_argument(
        "--top-candidates", type=int, default=3,
        help="How many filtered talking-head videos to keep (default: 3)",
    )
    parser.add_argument(
        "--generate-count", type=int, default=1,
        help="How many avatar videos to generate (default: 1)",
    )
    parser.add_argument(
        "--min-score", type=int, default=50,
        help="Minimum talking head composite score (default: 50)",
    )

    # Gender-based avatar selection
    parser.add_argument(
        "--avatar-male",
        help="Path to male avatar image (auto-selected when source person is male)",
    )
    parser.add_argument(
        "--avatar-female",
        help="Path to female avatar image (auto-selected when source person is female)",
    )

    # Flags
    parser.add_argument(
        "--skip-generate", action="store_true",
        help="Stop after filtering — do not run Higgsfield generation",
    )
    parser.add_argument(
        "--enable-analysis", action="store_true",
        help="Enable Claude Vision analysis + auto-fix after generation",
    )
    parser.add_argument(
        "--output-dir", default=".tmp/tiktok_generated/",
        help="Output directory for generated videos (default: .tmp/tiktok_generated/)",
    )

    args = parser.parse_args()

    # Run the pipeline
    print(f"TikTok Avatar Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Avatar: {args.avatar}")
    if args.category:
        print(f"Mode: Full auto (category={args.category})")
    elif args.keyword:
        print(f"Mode: From keyword ({args.keyword})")
    elif args.videos_dir:
        print(f"Mode: From existing videos ({args.videos_dir})")
    print()

    results = run_pipeline(args)

    # Save summary JSON
    save_pipeline_summary(results, args.output_dir)

    if not results:
        print("\nPipeline finished with no generated outputs.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
