#!/usr/bin/env python3
"""
Generate a CapCut Desktop project from rendered scene clips + narration + SFX.

Usage:
  python3 execution/generate_capcut_project.py \
    --name "RAG Agent" \
    --scenes-dir .tmp/ragagent/scenes \
    --narration-dir yt-growth-chart/public/narration-ragagent \
    --sfx-dir yt-growth-chart/public/sfx-ragagent \
    --num-scenes 12
"""

import argparse
import json
import os
import shutil
import subprocess
import time
import uuid


CAPCUT_ROOT = os.path.expanduser(
    "~/Movies/CapCut/User Data/Projects/com.lveditor.draft"
)


def uid():
    return str(uuid.uuid4()).upper()


def get_duration_us(filepath):
    """Get media duration in microseconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", filepath],
            capture_output=True, text=True, timeout=10
        )
        secs = float(result.stdout.strip())
        return int(secs * 1_000_000)
    except Exception:
        return 3_830_000  # fallback ~3.83s


def get_video_info(filepath):
    """Get video width/height."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "stream=width,height",
             "-of", "csv=p=0", filepath],
            capture_output=True, text=True, timeout=10
        )
        parts = result.stdout.strip().split(",")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 1080, 1920


def find_file(directory, base, extensions):
    """Find a file with one of the given extensions."""
    for ext in extensions:
        path = os.path.join(directory, f"{base}{ext}")
        if os.path.exists(path):
            return path
    return None


def make_video_material(path, duration_us, width, height):
    mid = uid()
    local_mid = str(uuid.uuid4())
    return {
        "aigc_type": "none",
        "audio_fade": None,
        "cartoon_path": "",
        "category_id": "",
        "category_name": "local",
        "check_flag": 62978047,
        "content_feature_info": None,
        "crop": {
            "lower_left_x": 0.0, "lower_left_y": 1.0,
            "lower_right_x": 1.0, "lower_right_y": 1.0,
            "upper_left_x": 0.0, "upper_left_y": 0.0,
            "upper_right_x": 1.0, "upper_right_y": 0.0
        },
        "crop_ratio": "free",
        "crop_scale": 1.0,
        "duration": duration_us,
        "extra_type_option": 0,
        "formula_id": "",
        "freeze": None,
        "has_audio": True,
        "height": height,
        "id": mid,
        "intensifies_audio_path": "",
        "intensifies_path": "",
        "is_ai_generate_content": False,
        "is_copyright": False,
        "is_text_edit_overdub": False,
        "is_unified_beauty_mode": False,
        "local_material_id": local_mid,
        "material_id": "",
        "material_name": os.path.basename(path),
        "material_url": "",
        "matting": {
            "flag": 0, "has_use_quick_brush": False,
            "has_use_quick_eraser": False, "interactiveTime": [],
            "path": "", "strokes": []
        },
        "media_path": "",
        "path": path,
        "picture_from": "none",
        "reverse_path": "",
        "source": 0,
        "source_platform": 0,
        "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": 0, "start": 0}},
        "type": "video",
        "video_algorithm": {
            "algorithms": [],
            "path": "",
            "time_range": None
        },
        "width": width
    }, mid


def make_audio_material(path, duration_us, name=""):
    mid = uid()
    local_mid = str(uuid.uuid4())
    return {
        "app_id": 0,
        "category_id": "",
        "category_name": "local",
        "check_flag": 1,
        "duration": duration_us,
        "effect_id": "",
        "formula_id": "",
        "id": mid,
        "intensifies_path": "",
        "local_material_id": local_mid,
        "music_id": "",
        "name": name or os.path.basename(path),
        "path": path,
        "request_id": "",
        "resource_id": "",
        "search_id": "",
        "source_from": "",
        "source_platform": 0,
        "team_id": "",
        "text_id": "",
        "tone_category_id": "",
        "tone_category_name": "",
        "tone_effect_id": "",
        "tone_effect_name": "",
        "tone_platform": "",
        "tone_second_category_id": "",
        "tone_second_category_name": "",
        "tone_speaker": "",
        "tone_type": "",
        "type": "extract_music",
        "video_id": "",
        "wave_points": []
    }, mid


def make_speed():
    sid = uid()
    return {"curve_speed": None, "id": sid, "mode": 0, "speed": 1.0, "type": "speed"}, sid


def make_canvas():
    cid = uid()
    return {
        "album_image": "", "blur": 0.0, "color": "", "id": cid,
        "image": "", "image_id": "", "image_name": "",
        "source_platform": 0, "team_id": "", "type": "canvas_color"
    }, cid


def make_sound_channel():
    sid = uid()
    return {"audio_channel_mapping": 0, "id": sid, "is_config_open": False, "type": ""}, sid


def make_vocal_sep():
    vid = uid()
    return {
        "choice": 0, "id": vid, "production_path": "",
        "removed_sounds": [], "time_range": None, "type": "vocal_separation"
    }, vid


def make_video_segment(material_id, start_us, duration_us, speed_id, canvas_id, scm_id, vocal_id, render_index=0):
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}
        },
        "common_keyframes": [],
        "enable_adjust": True,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_lut": True,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": [speed_id, canvas_id, scm_id, vocal_id],
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "id": uid(),
        "intensifies_audio": False,
        "is_placeholder": False,
        "keyframe_refs": [],
        "last_nonzero_volume": 1.0,
        "material_id": material_id,
        "render_index": render_index,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0
        },
        "reverse": False,
        "source_timerange": {"duration": duration_us, "start": 0},
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": duration_us, "start": start_us},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 0,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True,
        "volume": 0.0
    }


def make_audio_segment(material_id, start_us, duration_us, volume=1.0):
    return {
        "caption_info": None,
        "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}
        },
        "common_keyframes": [],
        "enable_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_color_curves": True,
        "enable_color_match_adjust": False,
        "enable_color_wheels": True,
        "enable_hsl": False,
        "enable_lut": True,
        "enable_smart_color_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": [],
        "group_id": "",
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "id": uid(),
        "intensifies_audio": False,
        "is_placeholder": False,
        "keyframe_refs": [],
        "last_nonzero_volume": volume,
        "material_id": material_id,
        "render_index": 0,
        "render_timerange": {"duration": 0, "start": 0},
        "responsive_layout": {
            "enable": False, "horizontal_pos_layout": 0,
            "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0
        },
        "reverse": False,
        "source_timerange": {"duration": duration_us, "start": 0},
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"duration": duration_us, "start": start_us},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 0,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True,
        "volume": volume
    }


def main():
    parser = argparse.ArgumentParser(description="Generate a CapCut project from rendered scenes + audio")
    parser.add_argument("--name", required=True, help="Project name (shown in CapCut)")
    parser.add_argument("--scenes-dir", required=True, help="Directory with scene_00.mp4, scene_01.mp4, ...")
    parser.add_argument("--narration-dir", required=True, help="Directory with scene_00.mp3, scene_01.mp3, ...")
    parser.add_argument("--sfx-dir", required=True, help="Directory with sfx_00.wav, sfx_01.wav, ...")
    parser.add_argument("--num-scenes", required=True, type=int, help="Number of scenes")
    parser.add_argument("--sfx-volume", type=float, default=0.4, help="SFX track volume (default: 0.4)")
    args = parser.parse_args()

    project_folder = os.path.join(CAPCUT_ROOT, args.name)
    scenes_dir = os.path.abspath(args.scenes_dir)
    narration_dir = os.path.abspath(args.narration_dir)
    sfx_dir = os.path.abspath(args.sfx_dir)

    # Collect media info
    video_paths = []
    video_durations = []
    narration_paths = []
    narration_durations = []
    sfx_paths = []
    sfx_durations = []

    print("Analyzing media files...")
    for i in range(args.num_scenes):
        vp = os.path.join(scenes_dir, f"scene_{i:02d}.mp4")
        np_ = os.path.join(narration_dir, f"scene_{i:02d}.mp3")
        sp = find_file(sfx_dir, f"sfx_{i:02d}", [".wav", ".mp3"])

        if not os.path.exists(vp):
            print(f"  WARNING: Missing video {vp}")
            continue

        vd = get_duration_us(vp)
        nd = get_duration_us(np_) if np_ and os.path.exists(np_) else 0
        sd = get_duration_us(sp) if sp else 0

        video_paths.append(vp)
        video_durations.append(vd)
        narration_paths.append(np_ if os.path.exists(np_) else None)
        narration_durations.append(nd)
        sfx_paths.append(sp)
        sfx_durations.append(sd)

        print(f"  Scene {i:02d}: video={vd/1e6:.2f}s  narration={nd/1e6:.2f}s  sfx={sd/1e6:.2f}s")

    if not video_paths:
        print("ERROR: No video files found!")
        return

    w, h = get_video_info(video_paths[0])
    total_duration = sum(video_durations)
    num = len(video_paths)
    print(f"\nTotal duration: {total_duration/1e6:.2f}s")
    print(f"Resolution: {w}x{h}")

    # Build materials
    video_materials = []
    video_material_ids = []
    audio_materials = []
    narration_material_ids = []
    sfx_material_ids = []
    speeds = []
    speed_ids = []
    canvases = []
    canvas_ids = []
    scm_list = []
    scm_ids = []
    vocal_list = []
    vocal_ids = []

    for i in range(num):
        vm, vmid = make_video_material(video_paths[i], video_durations[i], w, h)
        video_materials.append(vm)
        video_material_ids.append(vmid)

        if narration_paths[i]:
            nm, nmid = make_audio_material(narration_paths[i], narration_durations[i], f"Narration {i:02d}")
            audio_materials.append(nm)
            narration_material_ids.append(nmid)
        else:
            narration_material_ids.append(None)

        if sfx_paths[i]:
            sm, smid = make_audio_material(sfx_paths[i], sfx_durations[i], f"SFX {i:02d}")
            audio_materials.append(sm)
            sfx_material_ids.append(smid)
        else:
            sfx_material_ids.append(None)

        sp_obj, sp_id = make_speed()
        speeds.append(sp_obj)
        speed_ids.append(sp_id)

        c_obj, c_id = make_canvas()
        canvases.append(c_obj)
        canvas_ids.append(c_id)

        scm_obj, scm_id = make_sound_channel()
        scm_list.append(scm_obj)
        scm_ids.append(scm_id)

        v_obj, v_id = make_vocal_sep()
        vocal_list.append(v_obj)
        vocal_ids.append(v_id)

    # Build tracks
    # Video track
    video_segments = []
    timeline_pos = 0
    for i in range(num):
        seg = make_video_segment(
            video_material_ids[i], timeline_pos, video_durations[i],
            speed_ids[i], canvas_ids[i], scm_ids[i], vocal_ids[i], i
        )
        video_segments.append(seg)
        timeline_pos += video_durations[i]

    video_track = {
        "attribute": 0, "flag": 0, "id": uid(),
        "is_default_name": True, "name": "",
        "segments": video_segments, "type": "video"
    }

    # Narration audio track
    narration_segments = []
    timeline_pos = 0
    for i in range(num):
        if narration_material_ids[i]:
            seg = make_audio_segment(narration_material_ids[i], timeline_pos, narration_durations[i], volume=1.0)
            narration_segments.append(seg)
        timeline_pos += video_durations[i]

    narration_track = {
        "attribute": 0, "flag": 0, "id": uid(),
        "is_default_name": False, "name": "Narration",
        "segments": narration_segments, "type": "audio"
    }

    # SFX audio track
    sfx_segments = []
    timeline_pos = 0
    for i in range(num):
        if sfx_material_ids[i]:
            seg = make_audio_segment(sfx_material_ids[i], timeline_pos, sfx_durations[i], volume=args.sfx_volume)
            sfx_segments.append(seg)
        timeline_pos += video_durations[i]

    sfx_track = {
        "attribute": 0, "flag": 0, "id": uid(),
        "is_default_name": False, "name": "SFX",
        "segments": sfx_segments, "type": "audio"
    }

    # Build draft_info.json
    now_us = int(time.time() * 1_000_000)
    draft_id = uid()

    draft_info = {
        "canvas_config": {
            "background": None,
            "height": h,
            "ratio": "9:16",
            "width": w
        },
        "color_space": -1,
        "config": {
            "adjust_max_index": 1,
            "attachment_info": [],
            "combination_max_index": 1,
            "export_range": None,
            "extract_audio_last_index": 1,
            "lyrics_recognition_id": "",
            "lyrics_sync": True,
            "lyrics_taskinfo": [],
            "maintrack_adsorb": True,
            "material_save_mode": 0,
            "multi_language_current": "none",
            "multi_language_list": [],
            "multi_language_main": "none",
            "multi_language_mode": "none",
            "original_sound_last_index": 1,
            "record_audio_last_index": 1,
            "sticker_max_index": 1,
            "subtitle_keywords_config": None,
            "subtitle_recognition_id": "",
            "subtitle_sync": True,
            "subtitle_taskinfo": [],
            "system_font_list": [],
            "video_mute": False,
            "zoom_info_params": None
        },
        "cover": None,
        "create_time": 0,
        "draft_type": "video",
        "duration": total_duration,
        "extra_info": None,
        "fps": 30.0,
        "free_render_index_mode_on": False,
        "id": draft_id,
        "keyframe_graph_list": [],
        "keyframes": {
            "adjusts": [], "audios": [], "effects": [], "filters": [],
            "handwrites": [], "stickers": [], "texts": [], "videos": []
        },
        "last_modified_platform": {
            "app_id": 359289, "app_source": "cc", "app_version": "7.5.0",
            "device_id": "c4ca4238a0b923820dcc509a6f75849b",
            "hard_disk_id": "", "mac_address": "",
            "os": "mac", "os_version": "26.0.1"
        },
        "materials": {
            "ai_translates": [],
            "audio_balances": [],
            "audio_effects": [],
            "audio_fades": [],
            "audio_pannings": [],
            "audio_pitch_shifts": [],
            "audio_track_indexes": [],
            "audios": audio_materials,
            "beats": [],
            "canvases": canvases,
            "chromas": [],
            "color_curves": [],
            "drafts": [],
            "effects": [],
            "flowers": [],
            "green_screens": [],
            "handwrites": [],
            "hsl": [],
            "images": [],
            "loudnesses": [],
            "manual_deformations": [],
            "material_animations": [],
            "material_colors": [],
            "multi_language_refs": [],
            "placeholders": [],
            "plugin_effects": [],
            "realtime_denoises": [],
            "shapes": [],
            "smart_crops": [],
            "smart_relights": [],
            "sound_channel_mappings": scm_list,
            "speeds": speeds,
            "stickers": [],
            "tail_leaders": [],
            "text_templates": [],
            "texts": [],
            "time_marks": [],
            "transitions": [],
            "video_effects": [],
            "video_trackings": [],
            "videos": video_materials,
            "vocal_beautifys": [],
            "vocal_separations": vocal_list
        },
        "mutable_config": None,
        "name": "",
        "new_version": "148.0.0",
        "platform": {
            "app_id": 359289, "app_source": "cc", "app_version": "7.5.0",
            "device_id": "c4ca4238a0b923820dcc509a6f75849b",
            "hard_disk_id": "", "mac_address": "",
            "os": "mac", "os_version": "26.0.1"
        },
        "relationships": [],
        "render_index_track_mode_on": True,
        "retouch_cover": None,
        "source": "default",
        "static_cover_image_path": "",
        "time_marks": None,
        "tracks": [video_track, narration_track, sfx_track],
        "update_time": 0,
        "version": 360000
    }

    # Create project folder
    if os.path.exists(project_folder):
        shutil.rmtree(project_folder)
    os.makedirs(project_folder, exist_ok=True)

    # Copy media into Resources/ and rewrite paths
    resources_dir = os.path.join(project_folder, "Resources")
    os.makedirs(resources_dir, exist_ok=True)
    print("\nCopying media to Resources/...")
    all_materials = draft_info["materials"]["videos"] + draft_info["materials"]["audios"]
    for mat in all_materials:
        src = mat["path"]
        filename = os.path.basename(src)
        dst = os.path.join(resources_dir, filename)
        shutil.copy2(src, dst)
        mat["path"] = dst
        print(f"  {filename}")

    # Write draft_info.json
    with open(os.path.join(project_folder, "draft_info.json"), "w") as f:
        json.dump(draft_info, f, separators=(",", ":"))
    print(f"\nWrote draft_info.json")

    # Write draft_meta_info.json
    draft_meta = {
        "draft_cover": "",
        "draft_fold_path": project_folder,
        "draft_id": draft_id,
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_json_file": os.path.join(project_folder, "draft_info.json"),
        "draft_name": args.name,
        "draft_new_version": "",
        "draft_root_path": CAPCUT_ROOT,
        "draft_timeline_materials_size": 0,
        "draft_type": "",
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": total_duration
    }

    with open(os.path.join(project_folder, "draft_meta_info.json"), "w") as f:
        json.dump(draft_meta, f, separators=(",", ":"))
    print("Wrote draft_meta_info.json")

    # Update root_meta_info.json
    root_meta_path = os.path.join(CAPCUT_ROOT, "root_meta_info.json")
    if os.path.exists(root_meta_path):
        with open(root_meta_path, "r") as f:
            root_meta = json.load(f)
    else:
        root_meta = {"all_draft_store": []}

    # Remove any existing entry for this project
    root_meta["all_draft_store"] = [
        d for d in root_meta["all_draft_store"]
        if d.get("draft_name") != args.name
    ]

    # Add new entry at the top
    root_entry = {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "",
        "draft_fold_path": project_folder,
        "draft_id": draft_id,
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_invisible": False,
        "draft_is_web_article_video": False,
        "draft_json_file": os.path.join(project_folder, "draft_info.json"),
        "draft_name": args.name,
        "draft_new_version": "",
        "draft_root_path": CAPCUT_ROOT,
        "draft_timeline_materials_size": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "streaming_edit_draft_ready": True,
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": total_duration
    }
    root_meta["all_draft_store"].insert(0, root_entry)

    with open(root_meta_path, "w") as f:
        json.dump(root_meta, f, separators=(",", ":"))
    print("Updated root_meta_info.json")

    print(f"\nCapCut project '{args.name}' created!")
    print(f"  Location: {project_folder}")
    print(f"  Tracks: 1 video + 1 narration + 1 SFX")
    print(f"  Clips: {num} per track = {num * 3} total")
    print(f"  Duration: {total_duration/1e6:.2f}s")


if __name__ == "__main__":
    main()
