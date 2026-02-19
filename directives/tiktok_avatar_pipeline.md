# TikTok Shop → Avatar Video Pipeline

## Overview
Automatically find high-converting TikTok Shop product videos (single-person talking head format, 30-60s) and generate full-length avatar replacements using Higgsfield Kling Motion Control with parallel processing.

**Target: < 5 minutes per video, ~$0.87 cost per 30s video.**

## Prerequisites
- `APIFY_API_TOKEN` in `.env` (for TikTok scraping)
- `HF_KEY` in `.env` (for Higgsfield Kling Motion Control — get from cloud.higgsfield.ai)
- `GOOGLE_API_KEY` in `.env` (optional, for Nano Banana Pro fallback face swap)
- Avatar image at `tiktok-avatar-pipeline/avatar.png`
- `ffmpeg` installed (`brew install ffmpeg`)
- Python deps: `pip install -r requirements.txt`
- InsightFace models: `buffalo_l` + `inswapper_128.onnx` in `~/.insightface/models/`

## Pipeline Steps

### Step 1: Find Trending Products (Optional)
Scrape trending TikTok Shop products by category.

```bash
python3 execution/scrape_tiktok_products.py --category beauty --max_items 5
```

Output: `.tmp/tiktok_products_TIMESTAMP.json`

### Step 2: Scrape Product Videos (5 parallel downloads)
Find and download TikTok videos for a product keyword.

```bash
python3 execution/scrape_tiktok_videos.py --query "viral beauty serum" --max_videos 20 --download
```

Downloads use `ThreadPoolExecutor(max_workers=5)` for parallel I/O.

Output: `.tmp/tiktok_videos_TIMESTAMP.json` + `.tmp/tiktok_downloads/*.mp4`

### Step 3: Filter for Talking Head Videos (parallel + engagement ranking)
Analyze downloaded videos using `ProcessPoolExecutor(max_workers=4)` for parallel analysis.

```bash
python3 execution/filter_talking_head.py --videos-dir .tmp/tiktok_downloads/ --top 3
```

Scoring criteria:
- Single face in 70%+ of frames (40 points)
- Face size 15-40% of frame (25 points)
- Fewer than 3 scene cuts (20 points)
- Duration **30-60s** sweet spot (15 points) — hard cutoff 25-65s
- Pass threshold: score >= 50

When scrape metadata is available, candidates are ranked by:
- `final_rank = 0.6 * normalized_quality + 0.4 * normalized_engagement`
- Engagement = playCount + likes*5 + shares*10 + comments*3

### Step 4: Generate Full-Length Avatar Video (segment-based)
The new segment-based pipeline replaces the old single-clip generation:

```bash
python3 execution/segment_and_generate.py \
  --video .tmp/tiktok_downloads/best_video.mp4 \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --segment-duration 10
```

Sub-steps:
1. **Split** source video into 10s segments (`ffmpeg -f segment`)
2. **Face-swap** first frame of each segment using InsightFace inswapper (~1-2s per image, local CPU)
3. **Generate** all segments via Kling 3.0 Pro in parallel (`duration=10`, up to 6 concurrent)
4. **Stitch** generated segments + overlay original audio (`ffmpeg concat + audio merge`)

Output: `.tmp/tiktok_generated/final_VIDEO_TIMESTAMP.mp4`

### Full Pipeline (Automated)

```bash
# Full auto: trending products → videos → filter → segment → generate
python3 execution/tiktok_avatar_pipeline.py \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --category beauty --generate-count 1

# From keyword (skip product discovery)
python3 execution/tiktok_avatar_pipeline.py \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --keyword "viral beauty serum TikTok Shop"

# From existing downloaded videos
python3 execution/tiktok_avatar_pipeline.py \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --videos-dir .tmp/tiktok_downloads/

# Filter only (no generation — no Higgsfield cost)
python3 execution/tiktok_avatar_pipeline.py \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --keyword "viral serum" --skip-generate
```

## Face Swap Methods

### InsightFace (Default) — Local, Free, ~1-2s
Uses `buffalo_l` for face detection and `inswapper_128.onnx` for face swap.
- **Speed**: ~1-2s per image (CPU)
- **Cost**: Free (local inference)
- **Quality**: Purpose-built for face swap, sufficient for Kling reference images
- **Install**: `pip install insightface onnxruntime`

### Nano Banana Pro (Fallback) — API, ~$0.01-0.05, ~15-20s
Available via `--use-nano-banana` flag on `create_reference_image.py`.
- **Speed**: ~15-20s per image (API call)
- **Cost**: ~$0.01-0.05 per call
- **Quality**: Higher quality but much slower
- **Requires**: `GOOGLE_API_KEY` in `.env`

## Testing

### Quick test (each step independently)
1. `python3 execution/scrape_tiktok_products.py --category beauty --max_items 3`
2. `python3 execution/scrape_tiktok_videos.py --query "viral serum" --max_videos 5 --download`
3. `python3 execution/filter_talking_head.py --videos-dir .tmp/tiktok_downloads/ --top 3`
4. `python3 execution/create_reference_image.py --video <best_video> --avatar tiktok-avatar-pipeline/avatar.png`
5. `python3 execution/segment_and_generate.py --video <best_video> --avatar tiktok-avatar-pipeline/avatar.png`

### Verify final output
```bash
ffprobe -v quiet -show_format .tmp/tiktok_generated/final_*.mp4
```
Check: correct duration (matching source), has audio stream.

### Pipeline integration test
```bash
python3 execution/tiktok_avatar_pipeline.py \
  --avatar tiktok-avatar-pipeline/avatar.png \
  --videos-dir .tmp/tiktok_downloads/ --skip-generate
```

## Cost Estimates Per Video (30s source)

| Step | Count | Unit Cost | Total |
|------|-------|-----------|-------|
| InsightFace swap | 3 | Free | $0.00 |
| Kling 3.0 Pro (10s) | 3 | ~$0.29 | ~$0.87 |
| ffmpeg | 3 | Free | $0.00 |
| **Total** | | | **~$0.87** |

## Projected Timeline (30s source video)

```
Split into 10s segments (ffmpeg)          ~2s
InsightFace swap 3 frames (parallel)      ~3s
Kling 3.0 Pro × 3 segments (parallel)    ~170s
Stitch + audio overlay (ffmpeg)           ~5s
─────────────────────────────────────────
TOTAL                                     ~3 min  ✅ under 5 min
```

## Edge Cases & Notes
- **Multi-person videos**: Automatically rejected by filter (single_face_ratio < 0.7)
- **Multi-cut videos**: Rejected if scene_cuts >= 3
- **TikTok watermarks**: Don't affect motion control — it transfers motion, not pixels
- **Very short/long videos**: Filtered out (25-65s window)
- **Download failures**: Individual video download failures are logged but don't halt the pipeline
- **Face swap failures**: If InsightFace fails for a segment, pipeline uses raw avatar as fallback — no data loss
- **Segment generation failures**: If a Kling generation fails for one segment, the final video stitches remaining segments
- **Higgsfield model paths**: Use `kling-video/{version}/{pro|std}/image-to-video`. Current default: `kling-video/v3.0/pro/image-to-video`.
- **Higgsfield video uploads**: SDK only supports image/audio uploads. Videos must be hosted externally (catbox.moe) and passed as `video_url`.
- **InsightFace models**: Must be pre-downloaded to `~/.insightface/models/` (buffalo_l + inswapper_128.onnx)
- **Rate limits**: Apify has usage-based pricing, Higgsfield has free tier then per-generation
