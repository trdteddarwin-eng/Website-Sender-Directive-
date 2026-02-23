#!/usr/bin/env python3
"""
Deploy a single HTML file to Vercel via the REST API.

Usage:
    python3 upwork-auto-apply/vercel_deployer.py \
        --html-file .tmp/acme-plumbing/index.html \
        --project-name acme-plumbing-demo

Prerequisites:
    - VERCEL_TOKEN in .env
"""

import os
import sys
import json
import time
import base64
import argparse
import requests
from typing import Optional
from dotenv import load_dotenv

# Load .env from workspace root
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(ENV_PATH)

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_API_BASE = "https://api.vercel.com"


def _vercel_headers():
    """Return standard Vercel API headers."""
    return {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }


def deploy_site(html_content: str, project_name: str, team_id: str = None) -> Optional[str]:
    """Deploy an HTML file to Vercel.

    Args:
        html_content: The full HTML string to deploy
        project_name: Name for the deployment (used in URL, e.g., 'acme-plumbing-demo')
        team_id: Optional Vercel team ID

    Returns:
        Live URL (e.g., 'https://acme-plumbing-demo-xyz.vercel.app') or None on failure.
    """
    if not VERCEL_TOKEN:
        print("Error: VERCEL_TOKEN not set in .env", file=sys.stderr)
        return None

    # Sanitize project name for Vercel (lowercase, alphanumeric + hyphens, max 100 chars)
    clean_name = project_name.lower().strip()
    clean_name = "".join(c if c.isalnum() or c == "-" else "-" for c in clean_name)
    clean_name = clean_name.strip("-")[:100]

    if not clean_name:
        print("Error: Invalid project name after sanitization", file=sys.stderr)
        return None

    # Base64 encode the HTML content
    encoded_content = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")

    # Build deployment payload
    payload = {
        "name": clean_name,
        "files": [
            {
                "file": "index.html",
                "data": encoded_content,
            }
        ],
        "target": "production",
        "projectSettings": {
            "framework": None,
        },
    }

    # Build URL with optional team ID
    url = f"{VERCEL_API_BASE}/v13/deployments"
    if team_id:
        url += f"?teamId={team_id}"

    print(f"Deploying '{clean_name}' to Vercel...")

    try:
        resp = requests.post(
            url,
            headers=_vercel_headers(),
            json=payload,
            timeout=60,
        )

        if resp.status_code == 403:
            print(f"Error: Authentication failed. Check VERCEL_TOKEN.", file=sys.stderr)
            return None

        if resp.status_code == 409:
            # Project name conflict — might need to use existing project
            print(f"Warning: Conflict for '{clean_name}', retrying with unique suffix...", file=sys.stderr)
            clean_name = f"{clean_name}-{int(time.time()) % 10000}"
            payload["name"] = clean_name
            resp = requests.post(
                url,
                headers=_vercel_headers(),
                json=payload,
                timeout=60,
            )

        resp.raise_for_status()
        data = resp.json()

    except requests.exceptions.Timeout:
        print("Error: Vercel API request timed out (60s)", file=sys.stderr)
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error: Vercel API returned {resp.status_code}: {resp.text[:500]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: Vercel deployment failed: {e}", file=sys.stderr)
        return None

    deployment_id = data.get("id")
    deployment_url = data.get("url")
    deployment_state = data.get("readyState", data.get("state", "UNKNOWN"))

    if not deployment_url:
        print(f"Error: No URL in Vercel response: {json.dumps(data, indent=2)[:500]}", file=sys.stderr)
        return None

    # Ensure URL has https:// prefix
    if not deployment_url.startswith("http"):
        deployment_url = f"https://{deployment_url}"

    print(f"  Deployment ID: {deployment_id}")
    print(f"  State: {deployment_state}")

    # Poll for readiness if not already ready (usually instant for static files)
    if deployment_state not in ("READY", "ready"):
        print("  Waiting for deployment to be ready...", end="", file=sys.stderr)
        for _ in range(30):  # Max 60 seconds
            time.sleep(2)
            try:
                status_url = f"{VERCEL_API_BASE}/v13/deployments/{deployment_id}"
                if team_id:
                    status_url += f"?teamId={team_id}"
                status_resp = requests.get(
                    status_url,
                    headers=_vercel_headers(),
                    timeout=15,
                )
                status_resp.raise_for_status()
                state = status_resp.json().get("readyState", "UNKNOWN")
                if state in ("READY", "ready"):
                    print(" Ready!", file=sys.stderr)
                    break
                elif state in ("ERROR", "CANCELED"):
                    print(f"\n  Deployment failed with state: {state}", file=sys.stderr)
                    return None
                print(".", end="", file=sys.stderr, flush=True)
            except Exception:
                print("?", end="", file=sys.stderr, flush=True)
        else:
            print("\n  Warning: Deployment did not reach READY state within 60s", file=sys.stderr)
            print(f"  URL may still work: {deployment_url}", file=sys.stderr)

    print(f"  Live URL: {deployment_url}")
    return deployment_url


def cleanup_old_deployments(project_name: str, keep_latest: int = 5, team_id: str = None) -> int:
    """Delete old deployments for a project, keeping the N most recent.

    Args:
        project_name: The project name to clean up deployments for
        keep_latest: Number of most recent deployments to keep (default: 5)
        team_id: Optional Vercel team ID

    Returns:
        Number of deployments deleted.
    """
    if not VERCEL_TOKEN:
        print("Error: VERCEL_TOKEN not set in .env", file=sys.stderr)
        return 0

    # List deployments for the project
    url = f"{VERCEL_API_BASE}/v6/deployments"
    params = {"projectId": project_name, "limit": 100}
    if team_id:
        params["teamId"] = team_id

    try:
        resp = requests.get(
            url,
            headers=_vercel_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Error listing deployments: {e}", file=sys.stderr)
        return 0

    deployments = data.get("deployments", [])
    if not deployments:
        print(f"  No deployments found for project '{project_name}'")
        return 0

    # Sort by creation time descending (most recent first)
    deployments.sort(key=lambda d: d.get("created", 0), reverse=True)

    # Keep the N most recent, delete the rest
    to_delete = deployments[keep_latest:]
    if not to_delete:
        print(f"  Only {len(deployments)} deployment(s) found, nothing to clean up (keeping {keep_latest})")
        return 0

    deleted = 0
    for dep in to_delete:
        dep_id = dep.get("uid") or dep.get("id")
        dep_url = dep.get("url", "unknown")
        if not dep_id:
            continue

        try:
            delete_url = f"{VERCEL_API_BASE}/v13/deployments/{dep_id}"
            if team_id:
                delete_url += f"?teamId={team_id}"

            del_resp = requests.delete(
                delete_url,
                headers=_vercel_headers(),
                timeout=15,
            )

            if del_resp.status_code in (200, 204):
                deleted += 1
                print(f"  Deleted: {dep_url} ({dep_id})")
            else:
                print(f"  Failed to delete {dep_id}: {del_resp.status_code}", file=sys.stderr)

        except Exception as e:
            print(f"  Error deleting {dep_id}: {e}", file=sys.stderr)

    print(f"  Cleanup complete: {deleted}/{len(to_delete)} deployments deleted")
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Deploy an HTML file to Vercel")
    parser.add_argument("--html-file", required=True, help="Path to the HTML file to deploy")
    parser.add_argument("--project-name", required=True, help="Project/deployment name (used in URL)")
    parser.add_argument("--team-id", default=None, help="Optional Vercel team ID")
    parser.add_argument("--cleanup", action="store_true", help="Also clean up old deployments (keep latest 5)")

    args = parser.parse_args()

    # Read the HTML file
    if not os.path.isfile(args.html_file):
        print(f"Error: File not found: {args.html_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.html_file, "r") as f:
        html_content = f.read()

    if not html_content.strip():
        print("Error: HTML file is empty", file=sys.stderr)
        sys.exit(1)

    # Deploy
    url = deploy_site(
        html_content=html_content,
        project_name=args.project_name,
        team_id=args.team_id,
    )

    if not url:
        print("Deployment failed.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDeployed: {url}")

    # Optional cleanup
    if args.cleanup:
        print(f"\nCleaning up old deployments for '{args.project_name}'...")
        cleanup_old_deployments(args.project_name, keep_latest=5, team_id=args.team_id)


if __name__ == "__main__":
    main()
