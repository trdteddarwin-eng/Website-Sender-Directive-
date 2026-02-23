#!/usr/bin/env python3
"""
Generate animated flowchart video data for automation job proposals.
Uses Opus 4.6 via OpenRouter to analyze job and create flowchart definition,
then feeds it into a Remotion template for rendering.
"""

import os
import sys
import json
import argparse
import time
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-opus-4-6"


def generate_flowchart_data(job_title: str, job_description: str) -> Optional[dict]:
    """Generate flowchart nodes/edges from a job description.

    Returns:
        {
            'title': str,  # Short title for the flowchart
            'nodes': [
                {'id': 'n1', 'label': 'Lead Comes In', 'icon': 'inbox', 'color': '#4F46E5'},
                {'id': 'n2', 'label': 'AI Scores Lead', 'icon': 'brain', 'color': '#7C3AED'},
                ...
            ],
            'edges': [
                {'from': 'n1', 'to': 'n2', 'label': 'webhook'},
                {'from': 'n2', 'to': 'n3', 'label': 'if score > 7'},
                ...
            ],
            'style': 'horizontal' | 'vertical' | 'zigzag',
            'duration_seconds': 8
        }
    """
    # Prompt Opus 4.6 to:
    # 1. Read the job description
    # 2. Design a 4-6 step automation workflow that would solve the client's problem
    # 3. Return structured JSON with nodes (each has label, icon type, color) and edges (connections with labels)
    #
    # Icon types: 'inbox', 'brain', 'email', 'database', 'chart', 'gear', 'robot', 'phone', 'calendar', 'filter', 'send', 'check'
    #
    # The flowchart should look professional and show concrete steps, not generic ones

    prompt = f"""Analyze this Upwork job posting and design a 4-6 step automation flowchart showing how you would build the solution.

JOB TITLE: {job_title}
JOB DESCRIPTION: {job_description[:1500]}

Design a clear, professional flowchart with:
- 4-6 nodes (steps in the automation)
- Each node has a short label (2-4 words), an icon type, and a color
- Edges connecting nodes with short labels describing the data/trigger flow
- Pick a layout style that best fits the flow

Available icon types: inbox, brain, email, database, chart, gear, robot, phone, calendar, filter, send, check, webhook, api, spreadsheet, slack, crm

Return ONLY this JSON (no markdown, no explanation):
{{
    "title": "Short Flowchart Title",
    "nodes": [
        {{"id": "n1", "label": "Step Name", "icon": "icon_type", "color": "#hex"}},
        ...
    ],
    "edges": [
        {{"from": "n1", "to": "n2", "label": "trigger/data description"}},
        ...
    ],
    "style": "horizontal",
    "duration_seconds": 8
}}

Make the flowchart SPECIFIC to this job — use the actual tools/platforms mentioned. Use distinct colors for each node (blues, purples, greens, oranges). Keep labels concise."""

    for attempt in range(2):
        try:
            if attempt > 0:
                time.sleep(5)

            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown fences
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            data = json.loads(content)

            # Validate structure
            if not data.get("nodes") or len(data["nodes"]) < 3:
                print(f"  Too few nodes ({len(data.get('nodes', []))}), retrying...")
                continue

            return data

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")

    return None


def write_remotion_props(flowchart_data: dict, output_path: str) -> str:
    """Write flowchart data as Remotion input props JSON file.

    Returns: path to the props file
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(flowchart_data, f, indent=2)
    print(f"  Written props to {output_path}")
    return output_path


def render_flowchart_video(props_path: str, output_path: str, remotion_dir: str = None) -> Optional[str]:
    """Render the flowchart video using Remotion CLI.

    Returns: path to rendered video, or None on failure.
    """
    import subprocess

    if remotion_dir is None:
        remotion_dir = os.path.join(os.path.dirname(__file__), "remotion-flowchart")

    if not os.path.exists(remotion_dir):
        print(f"  Remotion project not found at {remotion_dir}")
        return None

    cmd = [
        "npx", "remotion", "render",
        "FlowchartVideo",
        output_path,
        "--props", props_path,
        "--codec", "h264",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=remotion_dir,
        )

        if result.returncode == 0:
            print(f"  Rendered video: {output_path}")
            return output_path
        else:
            print(f"  Render failed: {result.stderr[:500]}")
            return None
    except subprocess.TimeoutExpired:
        print("  Render timed out (120s)")
        return None


def generate_flowchart_for_job(
    job_title: str,
    job_description: str,
    output_dir: str = ".tmp/flowcharts",
    render: bool = False,
) -> dict:
    """Full pipeline: generate data -> optionally render video.

    Returns:
        {
            'props_path': str,
            'video_path': str | None,
            'flowchart_data': dict,
            'success': bool
        }
    """
    # Generate slug from job title
    slug = job_title.lower()[:40].strip()
    for ch in " /\\:*?\"<>|":
        slug = slug.replace(ch, "-")
    slug = "-".join(filter(None, slug.split("-")))

    os.makedirs(output_dir, exist_ok=True)

    # Generate flowchart data
    print(f"Generating flowchart for: {job_title[:50]}...")
    data = generate_flowchart_data(job_title, job_description)

    if not data:
        return {"props_path": None, "video_path": None, "flowchart_data": None, "success": False}

    # Write props
    props_path = os.path.join(output_dir, f"{slug}-props.json")
    write_remotion_props(data, props_path)

    # Optionally render
    video_path = None
    if render:
        video_output = os.path.join(output_dir, f"{slug}.mp4")
        video_path = render_flowchart_video(props_path, video_output)

    return {
        "props_path": props_path,
        "video_path": video_path,
        "flowchart_data": data,
        "success": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate automation flowchart video")
    parser.add_argument("--job-title", "-t", required=True, help="Job title")
    parser.add_argument("--job-description", "-d", required=True, help="Job description (or path to .txt file)")
    parser.add_argument("--output-dir", "-o", default=".tmp/flowcharts", help="Output directory")
    parser.add_argument("--render", action="store_true", help="Also render the video")

    args = parser.parse_args()

    # Read description from file if it's a path
    desc = args.job_description
    if os.path.exists(desc):
        with open(desc) as f:
            desc = f.read()

    result = generate_flowchart_for_job(
        job_title=args.job_title,
        job_description=desc,
        output_dir=args.output_dir,
        render=args.render,
    )

    if result["success"]:
        print(f"\nFlowchart generated successfully!")
        print(f"  Nodes: {len(result['flowchart_data']['nodes'])}")
        print(f"  Props: {result['props_path']}")
        if result["video_path"]:
            print(f"  Video: {result['video_path']}")
    else:
        print("\nFailed to generate flowchart")
        sys.exit(1)
