#!/usr/bin/env python3
"""
Deploy a spec site to Netlify via the Netlify CLI or API.

Uses Netlify's manual deploy (no Git required) — uploads a directory directly.

Usage:
    python3 execution/deploy_spec_site.py \
        --html .tmp/acme-hvac/index.html \
        --slug acme-hvac

    # With a custom Netlify site name:
    python3 execution/deploy_spec_site.py \
        --html .tmp/acme-hvac/index.html \
        --slug acme-hvac \
        --site_id tedca-spec-sites

Prerequisites:
    - NETLIFY_AUTH_TOKEN in .env (personal access token from app.netlify.com/user/applications)
    - NETLIFY_SITE_ID in .env (the API ID of the Netlify site to deploy to)
    OR
    - Netlify CLI: npm install -g netlify-cli && netlify login
"""

import os
import sys
import json
import shutil
import argparse
import tempfile
from dotenv import load_dotenv

load_dotenv()


def deploy_via_api(html_path, slug, site_id=None, auth_token=None):
    """
    Deploy spec site to Netlify using the deploy API.
    Deploys the HTML file under /{slug}/index.html on the Netlify site.

    Args:
        html_path: Path to the spec site index.html
        slug: URL slug (e.g., "acme-hvac")
        site_id: Netlify site API ID (from .env or arg)
        auth_token: Netlify auth token (from .env or arg)

    Returns:
        dict with deploy_url, site_url, slug
    """
    import requests
    import hashlib

    auth_token = auth_token or os.getenv("NETLIFY_AUTH_TOKEN")
    site_id = site_id or os.getenv("NETLIFY_SITE_ID")

    if not auth_token:
        print("Error: NETLIFY_AUTH_TOKEN not set in .env", file=sys.stderr)
        return None
    if not site_id:
        print("Error: NETLIFY_SITE_ID not set in .env", file=sys.stderr)
        return None

    if not os.path.exists(html_path):
        print(f"Error: HTML file not found: {html_path}", file=sys.stderr)
        return None

    # Read HTML content
    with open(html_path, "r") as f:
        html_content = f.read()

    # Create a temporary deploy directory with the slug structure
    with tempfile.TemporaryDirectory() as tmpdir:
        slug_dir = os.path.join(tmpdir, slug)
        os.makedirs(slug_dir)
        target_html = os.path.join(slug_dir, "index.html")
        with open(target_html, "w") as f:
            f.write(html_content)

        # Calculate file hash (SHA1 for Netlify digest)
        file_path_in_site = f"/{slug}/index.html"
        sha1 = hashlib.sha1(html_content.encode("utf-8")).hexdigest()

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Create a new deploy with file digest
        print(f"Deploying {slug} to Netlify site {site_id}...")
        deploy_data = {
            "files": {
                file_path_in_site: sha1,
            },
        }

        resp = requests.post(
            f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
            headers=headers,
            json=deploy_data,
            timeout=30,
        )
        resp.raise_for_status()
        deploy = resp.json()
        deploy_id = deploy["id"]

        # Upload the file
        required = deploy.get("required", [])
        if sha1 in required:
            print(f"  Uploading {file_path_in_site}...")
            upload_resp = requests.put(
                f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files{file_path_in_site}",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/octet-stream",
                },
                data=html_content.encode("utf-8"),
                timeout=30,
            )
            upload_resp.raise_for_status()

        # Get the deploy URL
        site_url = deploy.get("ssl_url") or deploy.get("url", "")
        deploy_url = f"{site_url}/{slug}/"

        print(f"  Deployed: {deploy_url}")
        return {
            "deploy_url": deploy_url,
            "site_url": site_url,
            "deploy_id": deploy_id,
            "slug": slug,
        }


def deploy_via_cli(html_path, slug, site_name=None):
    """
    Deploy spec site using Netlify CLI (fallback method).
    Creates a temporary directory structure and uses `netlify deploy --prod`.

    Args:
        html_path: Path to index.html
        slug: URL slug
        site_name: Optional Netlify site name

    Returns:
        dict with deploy_url, slug
    """
    import subprocess

    # Check if netlify CLI is available
    result = subprocess.run(["which", "netlify"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: netlify CLI not found. Install with: npm install -g netlify-cli", file=sys.stderr)
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create slug subdirectory
        slug_dir = os.path.join(tmpdir, slug)
        os.makedirs(slug_dir)
        shutil.copy2(html_path, os.path.join(slug_dir, "index.html"))

        # Deploy
        cmd = ["netlify", "deploy", "--prod", "--dir", tmpdir]
        if site_name:
            cmd.extend(["--site", site_name])

        print(f"Deploying via netlify CLI...")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if proc.returncode != 0:
            print(f"Error: netlify deploy failed: {proc.stderr}", file=sys.stderr)
            return None

        # Parse URL from output
        for line in proc.stdout.split("\n"):
            if "Website URL:" in line or "https://" in line.lower():
                url = line.strip().split()[-1]
                if url.startswith("http"):
                    return {
                        "deploy_url": f"{url}/{slug}/",
                        "site_url": url,
                        "slug": slug,
                    }

        return {"deploy_url": "", "slug": slug, "output": proc.stdout}


def main():
    parser = argparse.ArgumentParser(description="Deploy spec site to Netlify")
    parser.add_argument("--html", required=True, help="Path to index.html")
    parser.add_argument("--slug", required=True, help="URL slug (e.g., acme-hvac)")
    parser.add_argument("--site_id", help="Netlify site API ID (overrides .env)")
    parser.add_argument("--auth_token", help="Netlify auth token (overrides .env)")
    parser.add_argument("--method", choices=["api", "cli"], default="api", help="Deploy method (default: api)")
    parser.add_argument("--output", help="Save deploy info to JSON file")

    args = parser.parse_args()

    if args.method == "api":
        result = deploy_via_api(args.html, args.slug, args.site_id, args.auth_token)
    else:
        result = deploy_via_cli(args.html, args.slug)

    if result:
        print(f"\nDeploy successful!")
        print(f"  URL: {result.get('deploy_url', 'N/A')}")

        if args.output:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  Info saved to: {args.output}")
    else:
        print("Deploy failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
