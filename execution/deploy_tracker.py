"""Deploy email open-tracking pixel to a dedicated Netlify site.

Usage:
    python3 execution/deploy_tracker.py

Creates a temp copy of netlify-tracker/ with Supabase credentials baked
into the function (free Netlify plan doesn't support API env vars), then
deploys via `netlify deploy --prod`. Saves TRACKER_BASE_URL to .env.

Requires: netlify-cli (`npm install -g netlify-cli`)
"""

import os
import shutil
import subprocess
import requests
from dotenv import load_dotenv, set_key

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(WORKSPACE, ".env")
load_dotenv(ENV_PATH)

NETLIFY_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
TRACKER_SITE_ID = os.getenv("NETLIFY_TRACKER_SITE_ID", "")

API = "https://api.netlify.com/api/v1"
HEADERS = {"Authorization": f"Bearer {NETLIFY_TOKEN}"}

TRACKER_DIR = os.path.join(WORKSPACE, "netlify-tracker")
DEPLOY_DIR = os.path.join(WORKSPACE, ".tmp", "netlify-tracker-deploy")


def _create_site():
    """Create a new Netlify site for the tracker via API."""
    print("[deploy] Creating new Netlify site for tracker...")
    resp = requests.post(
        f"{API}/sites",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"name": "", "body": {"name": ""}},
    )
    resp.raise_for_status()
    site = resp.json()
    site_id = site["id"]
    url = site["ssl_url"] or site["url"]
    print(f"[deploy] Created site: {url} (id={site_id})")
    return site_id, url


def _build_deploy_copy():
    """Copy netlify-tracker/ and bake Supabase credentials into the function."""
    if os.path.exists(DEPLOY_DIR):
        shutil.rmtree(DEPLOY_DIR)
    shutil.copytree(TRACKER_DIR, DEPLOY_DIR)

    func_path = os.path.join(DEPLOY_DIR, "netlify", "functions", "track.js")
    with open(func_path) as f:
        code = f.read()

    code = code.replace(
        'const supabaseUrl = process.env.SUPABASE_URL;',
        f'const supabaseUrl = process.env.SUPABASE_URL || "{SUPABASE_URL}";',
    )
    code = code.replace(
        'const supabaseKey = process.env.SUPABASE_KEY;',
        f'const supabaseKey = process.env.SUPABASE_KEY || "{SUPABASE_KEY}";',
    )

    with open(func_path, "w") as f:
        f.write(code)
    print("[deploy] Built deploy copy with baked-in credentials")


def _deploy(site_id):
    """Deploy via Netlify CLI."""
    print("[deploy] Deploying via netlify-cli...")
    env = {**os.environ, "NETLIFY_AUTH_TOKEN": NETLIFY_TOKEN}
    result = subprocess.run(
        [
            "netlify", "deploy", "--prod",
            "--dir=.", "--functions=netlify/functions",
            f"--site={site_id}",
        ],
        cwd=DEPLOY_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"[deploy] ERROR: {result.stderr[-300:]}")
    return result.returncode == 0


def main():
    if not NETLIFY_TOKEN:
        print("ERROR: NETLIFY_AUTH_TOKEN not set in .env")
        return

    site_id = TRACKER_SITE_ID
    site_url = ""

    if not site_id:
        site_id, site_url = _create_site()
        set_key(ENV_PATH, "NETLIFY_TRACKER_SITE_ID", site_id)
        print(f"[deploy] Saved NETLIFY_TRACKER_SITE_ID={site_id} to .env")
    else:
        resp = requests.get(f"{API}/sites/{site_id}", headers=HEADERS)
        resp.raise_for_status()
        site = resp.json()
        site_url = site.get("ssl_url") or site.get("url", "")
        print(f"[deploy] Using existing site: {site_url}")

    _build_deploy_copy()
    success = _deploy(site_id)

    # Cleanup
    if os.path.exists(DEPLOY_DIR):
        shutil.rmtree(DEPLOY_DIR)

    if success:
        set_key(ENV_PATH, "TRACKER_BASE_URL", site_url)
        print(f"\n[deploy] Done! TRACKER_BASE_URL={site_url}")
        print(f"[deploy] Tracking pixel: {site_url}/.netlify/functions/track?t={{email_id}}")
    else:
        print("\n[deploy] Deploy failed — check errors above")


if __name__ == "__main__":
    main()
