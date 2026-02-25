# CapCut Export Directive

## Purpose
Export any Remotion video as a CapCut Desktop project — individual scene clips placed on a timeline with narration and SFX on separate tracks. CapCut handles transitions, captions, and effects.

## Prerequisites
- CapCut Desktop installed (macOS)
- ffprobe available (via ffmpeg)
- Rendered scene clips (`.mp4`), narration (`.mp3`), and SFX (`.wav`)

## Workflow

### Step 1: Render Individual Scenes
Render each scene as a separate clip from Remotion:
```bash
SD=115  # scene duration in frames (adjust per video)
NUM=12  # number of scenes
for i in $(seq 0 $((NUM - 1))); do
  start=$((i * SD))
  end=$((start + SD - 1))
  npx remotion render <CompositionId> .tmp/<slug>/scenes/scene_$(printf "%02d" $i).mp4 --frames=$start-$end
done
```

### Step 2: Generate CapCut Project
```bash
python3 execution/generate_capcut_project.py \
  --name "Project Name" \
  --scenes-dir .tmp/<slug>/scenes \
  --narration-dir yt-growth-chart/public/narration-<slug> \
  --sfx-dir yt-growth-chart/public/sfx-<slug> \
  --num-scenes <N>
```

### Step 3: Open CapCut Desktop
- The project appears in CapCut's project list immediately
- All media is copied into `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<name>/Resources/`
- Three tracks: Video, Narration (audio), SFX (audio)

### Step 4: Post-Production in CapCut
- Add 2-second cross-dissolve transitions between scenes
- Add auto-captions
- Adjust SFX volume if needed
- Export final video

## Script Details

**Script:** `execution/generate_capcut_project.py`

**What it does:**
1. Uses ffprobe to get exact durations of all media files
2. Builds CapCut's `draft_info.json` with video + narration + SFX tracks
3. Copies all media into the project's `Resources/` directory
4. Creates `draft_meta_info.json` metadata
5. Updates `root_meta_info.json` so CapCut discovers the project

**CLI Arguments:**
| Arg | Description |
|-----|-------------|
| `--name` | Project name (shown in CapCut) |
| `--scenes-dir` | Directory containing `scene_00.mp4`, `scene_01.mp4`, ... |
| `--narration-dir` | Directory containing `scene_00.mp3`, `scene_01.mp3`, ... |
| `--sfx-dir` | Directory containing `sfx_00.wav`, `sfx_01.wav`, ... |
| `--num-scenes` | Number of scenes |
| `--sfx-volume` | SFX track volume 0.0-1.0 (default: 0.4) |

## Edge Cases
- If a narration or SFX file is missing, the script skips that clip on the track
- SFX files can be `.wav` or `.mp3` — script checks both extensions
- If CapCut is open during injection, close and reopen it for the project to appear
- The script removes any existing project with the same name before creating

## File Naming Convention
- Scenes: `scene_00.mp4`, `scene_01.mp4`, ...
- Narration: `scene_00.mp3`, `scene_01.mp3`, ...
- SFX: `sfx_00.wav`, `sfx_01.wav`, ...
