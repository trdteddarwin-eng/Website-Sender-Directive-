#!/usr/bin/env python3
"""
Modal deployment for Upwork Auto-Apply Pipeline.

Deploys the pipeline as a scheduled Modal function that runs every 2 hours
during business hours (Mon-Fri, 9AM-6PM EST).

Usage:
    modal deploy upwork-auto-apply/modal_deploy.py     # Deploy to Modal
    modal run upwork-auto-apply/modal_deploy.py        # One-shot run
"""

import modal

# Build the Modal image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "wget", "gnupg", "ca-certificates",
        # Chromium dependencies for Playwright
        "libnss3", "libnspr4", "libatk1.0-0", "libatk-bridge2.0-0",
        "libcups2", "libdrm2", "libxkbcommon0", "libxcomposite1",
        "libxdamage1", "libxfixes3", "libxrandr2", "libgbm1",
        "libpango-1.0-0", "libcairo2", "libasound2",
        "libatspi2.0-0", "libwayland-client0",
    )
    .pip_install(
        "anthropic",
        "requests",
        "python-dotenv",
        "supabase",
        "playwright",
    )
    .run_commands("playwright install chromium")
)

app = modal.App("upwork-auto-apply", image=image)

# Mount the project directory
project_mount = modal.Mount.from_local_dir(
    "/Users/yoljean/Downloads/Ted Workspace/upwork-auto-apply",
    remote_path="/app/upwork-auto-apply",
)

# Mount execution scripts (needed for scraper imports)
execution_mount = modal.Mount.from_local_dir(
    "/Users/yoljean/Downloads/Ted Workspace/execution",
    remote_path="/app/execution",
)

# Secrets from .env
secrets = modal.Secret.from_dotenv(
    path="/Users/yoljean/Downloads/Ted Workspace/.env"
)


@app.function(
    mounts=[project_mount, execution_mount],
    secrets=[secrets],
    timeout=1800,  # 30 min max
    schedule=modal.Cron("0 */2 14-23 * * 1-5"),  # Every 2h, Mon-Fri, 9AM-6PM EST (14-23 UTC)
)
def run_pipeline():
    """Scheduled pipeline execution."""
    import sys
    sys.path.insert(0, "/app/upwork-auto-apply")
    sys.path.insert(0, "/app/execution")

    from pipeline import run, load_config

    config = load_config("/app/upwork-auto-apply/config.json")
    run(config=config)


@app.function(
    mounts=[project_mount, execution_mount],
    secrets=[secrets],
    timeout=1800,
)
@modal.web_endpoint(method="POST")
def trigger(request: dict = {}):
    """Manual trigger via POST webhook.

    POST body (all optional):
    {
        "dry_run": false,
        "with_deliverables": false,
        "limit": null,
        "headed": false
    }
    """
    import sys
    sys.path.insert(0, "/app/upwork-auto-apply")
    sys.path.insert(0, "/app/execution")

    from pipeline import run, load_config

    config = load_config("/app/upwork-auto-apply/config.json")

    try:
        run(
            config=config,
            dry_run=request.get("dry_run", False),
            with_deliverables=request.get("with_deliverables", False),
            limit=request.get("limit"),
        )
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.function(
    mounts=[project_mount, execution_mount],
    secrets=[secrets],
    timeout=300,
)
@modal.web_endpoint(method="GET")
def status():
    """Check pipeline status -- returns today's stats from Supabase."""
    import sys
    sys.path.insert(0, "/app/upwork-auto-apply")

    from tracker import get_daily_stats

    stats = get_daily_stats()
    return stats


@app.local_entrypoint()
def main():
    """Run pipeline once locally (for testing)."""
    run_pipeline.remote()
