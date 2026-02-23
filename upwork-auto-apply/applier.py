#!/usr/bin/env python3
"""
Playwright automation for Upwork job applications.

Uses saved session cookies (via session_manager) and externalized CSS selectors
(via selector_config.json) to apply to Upwork jobs with stealth settings.

Usage:
    python applier.py --job-url "https://www.upwork.com/..." --cover-letter "..." --rate 75
    python applier.py --job-url "..." --cover-letter "..." --rate 75 --headed --screenshot-dir ./screenshots
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(
        "ERROR: Playwright is not installed.\n"
        "Install it with:  pip install playwright && playwright install chromium"
    )
    sys.exit(1)

# Try to import stealth plugin; fall back to manual stealth if unavailable
try:
    from playwright_stealth import stealth_sync

    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

import session_manager

# Optional import for budget tracking
try:
    import tracker
except ImportError:
    tracker = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_selectors() -> dict:
    """Load CSS selectors from selector_config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "selector_config.json")
    with open(config_path, "r") as f:
        return json.load(f)


def human_type(page, selector: str, text: str, delay_ms: int = 20):
    """Type text with human-like delays (random variation around delay_ms).

    Clears existing content first, then types character by character.
    """
    element = page.locator(selector).first
    element.click()
    element.fill("")  # Clear existing content
    for char in text:
        element.type(char, delay=delay_ms + random.randint(-10, 30))
        # Occasional micro-pause to mimic thinking
        if random.random() < 0.05:
            time.sleep(random.uniform(0.2, 0.6))


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def verify_session(page) -> bool:
    """Check if we're logged in by looking for user menu element or URL."""
    selectors = load_selectors()
    login_check = selectors.get("login_check", {})

    # Check URL for login redirect
    current_url = page.url
    login_redirect = login_check.get("login_redirect", "/ab/account-security/login")
    if login_redirect in current_url:
        return False

    # Check for logged-in indicator element
    indicator_selector = login_check.get(
        "logged_in_indicator",
        "[data-test='user-menu'], .nav-user-menu, .user-avatar",
    )
    try:
        page.wait_for_selector(indicator_selector, timeout=5000)
        return True
    except PlaywrightTimeout:
        return False


def check_connects_cost(page) -> Optional[int]:
    """Read the connects cost from the apply page. Returns int or None."""
    selectors = load_selectors()
    cost_selector = selectors["apply_page"].get(
        "connects_cost_display",
        "[data-test='connects-cost'], .connects-required",
    )
    try:
        element = page.locator(cost_selector).first
        element.wait_for(timeout=5000)
        text = element.inner_text()
        # Extract number from text like "6 Connects" or "Connects: 6"
        import re
        numbers = re.findall(r"\d+", text)
        return int(numbers[0]) if numbers else None
    except Exception:
        return None


def _take_screenshot(page, screenshot_dir: str, label: str) -> Optional[str]:
    """Take a screenshot and return the file path."""
    if not screenshot_dir:
        return None
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(screenshot_dir, f"{label}_{timestamp}.png")
    try:
        page.screenshot(path=path, full_page=True)
        return path
    except Exception as e:
        print(f"[applier] Screenshot failed: {e}")
        return None


def _apply_stealth(context):
    """Apply stealth settings to a browser context's pages."""
    if HAS_STEALTH:
        # stealth_sync works on pages, so we apply it per-page via event
        context.on("page", lambda p: stealth_sync(p))
    # Manual stealth fallback is handled via browser launch args and context settings


# ---------------------------------------------------------------------------
# Core apply logic
# ---------------------------------------------------------------------------

def apply_to_job(
    page,
    job_url: str,
    cover_letter: str,
    hourly_rate: float = None,
    fixed_bid: float = None,
    skip_boost: bool = True,
    screenshot_dir: str = None,
) -> dict:
    """Apply to a single Upwork job.

    Args:
        page: Playwright page object (already authenticated).
        job_url: Full URL to the job apply page.
        cover_letter: Cover letter text.
        hourly_rate: Hourly rate to bid (for hourly jobs).
        fixed_bid: Fixed price bid (for fixed-price jobs).
        skip_boost: If True, ensure boost is turned off.
        screenshot_dir: Directory to save screenshots (optional).

    Returns:
        {
            'success': bool,
            'connects_spent': int,
            'error': str | None,
            'screenshot': str | None,
        }
    """
    selectors = load_selectors()
    apply_sel = selectors["apply_page"]
    result = {
        "success": False,
        "connects_spent": 0,
        "error": None,
        "screenshot": None,
    }

    try:
        # 1. Navigate to job apply URL
        # Ensure URL points to the apply page
        if "/apply/" not in job_url and "/proposals/" not in job_url:
            # Convert job view URL to apply URL
            job_url = job_url.rstrip("/") + "/apply/"

        print(f"[applier] Navigating to: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        random_delay(2.0, 4.0)

        # 2. Verify session is valid (not redirected to login)
        if not verify_session(page):
            result["error"] = "Session expired - redirected to login page"
            return result

        # 3. Read connects cost
        connects_cost = check_connects_cost(page)
        if connects_cost is not None:
            print(f"[applier] Connects cost: {connects_cost}")
            result["connects_spent"] = connects_cost

        # 4. Fill cover letter
        print("[applier] Filling cover letter...")
        try:
            human_type(page, apply_sel["cover_letter_textarea"], cover_letter)
            random_delay(1.0, 2.0)
        except Exception as e:
            result["error"] = f"Failed to fill cover letter: {e}"
            result["screenshot"] = _take_screenshot(page, screenshot_dir, "error_cover_letter")
            return result

        # 5. Set hourly rate or fixed bid
        if hourly_rate is not None:
            print(f"[applier] Setting hourly rate: ${hourly_rate}")
            try:
                rate_input = page.locator(apply_sel["hourly_rate_input"]).first
                rate_input.click()
                rate_input.fill("")
                rate_input.type(str(hourly_rate))
                random_delay(0.5, 1.5)
            except Exception as e:
                print(f"[applier] Warning: Could not set hourly rate: {e}")

        if fixed_bid is not None:
            print(f"[applier] Setting fixed bid: ${fixed_bid}")
            try:
                bid_input = page.locator(apply_sel["fixed_price_input"]).first
                bid_input.click()
                bid_input.fill("")
                bid_input.type(str(fixed_bid))
                random_delay(0.5, 1.5)
            except Exception as e:
                print(f"[applier] Warning: Could not set fixed bid: {e}")

        # 6. Ensure boost is off
        if skip_boost:
            try:
                boost_toggle = page.locator(apply_sel["boost_toggle"]).first
                if boost_toggle.is_visible(timeout=3000):
                    # Check if boost is currently on and turn it off
                    boost_off = page.locator(apply_sel["boost_off_option"]).first
                    if boost_off.is_visible(timeout=2000):
                        boost_off.click()
                        random_delay(0.5, 1.0)
                        print("[applier] Boost turned off.")
            except Exception:
                # Boost toggle may not be present on all listings
                pass

        # 7. Pre-submit screenshot
        pre_screenshot = _take_screenshot(page, screenshot_dir, "pre_submit")
        random_delay(1.0, 2.0)

        # 8. Click submit
        print("[applier] Submitting proposal...")
        try:
            submit_btn = page.locator(apply_sel["submit_button"]).first
            submit_btn.scroll_into_view_if_needed()
            random_delay(0.5, 1.0)
            submit_btn.click()
        except Exception as e:
            result["error"] = f"Failed to click submit: {e}"
            result["screenshot"] = _take_screenshot(page, screenshot_dir, "error_submit")
            return result

        # 9. Wait for success indicator
        try:
            page.wait_for_selector(
                apply_sel["success_indicator"],
                timeout=15000,
            )
            result["success"] = True
            print("[applier] Proposal submitted successfully!")
        except PlaywrightTimeout:
            # Check for error message
            try:
                error_el = page.locator(apply_sel["error_message"]).first
                if error_el.is_visible(timeout=3000):
                    result["error"] = f"Submit error: {error_el.inner_text()}"
                else:
                    result["error"] = "Timed out waiting for success confirmation"
            except Exception:
                result["error"] = "Timed out waiting for success confirmation"

        # 10. Post-submit screenshot
        post_screenshot = _take_screenshot(page, screenshot_dir, "post_submit")
        result["screenshot"] = post_screenshot or pre_screenshot

    except PlaywrightTimeout as e:
        result["error"] = f"Page timeout: {e}"
        result["screenshot"] = _take_screenshot(page, screenshot_dir, "error_timeout")
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        result["screenshot"] = _take_screenshot(page, screenshot_dir, "error_unexpected")

    return result


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_apply_batch(
    jobs: list[dict],
    config: dict,
    session_name: str = "default",
    headed: bool = False,
    screenshot_dir: str = None,
) -> list[dict]:
    """Apply to a batch of jobs sequentially with random delays.

    Args:
        jobs: List of dicts, each with:
            - apply_url: str
            - cover_letter: str
            - hourly_rate: float (optional)
            - fixed_bid: float (optional)
            - job_id: str
            - connects_cost: int (optional)
        config: Pipeline config dict. Expects config['auto_apply'] with:
            - delay_between_applies_sec: [min, max] or int
            - skip_boost: bool
            - default_hourly_rate: float
            - daily_application_limit: int
            - daily_connects_budget: int
        session_name: Which saved session to use.
        headed: If True, run browser in visible mode (for debugging).
        screenshot_dir: Directory to save screenshots.

    Returns:
        List of result dicts: {job_id, success, connects_spent, error}
    """
    auto_config = config.get("auto_apply", {})
    skip_boost = auto_config.get("skip_boost", True)
    default_rate = auto_config.get("default_hourly_rate", 75)
    daily_limit = auto_config.get("daily_application_limit", 10)
    daily_budget = auto_config.get("daily_connects_budget", 40)

    delay_cfg = auto_config.get("delay_between_applies_sec", [45, 120])
    if isinstance(delay_cfg, list) and len(delay_cfg) == 2:
        delay_min, delay_max = delay_cfg
    else:
        delay_min = delay_max = int(delay_cfg)

    # Load session
    session = session_manager.load_session(session_name)
    if not session:
        print(f"[applier] No valid session found for '{session_name}'. Run login_helper.py first.")
        return [{"job_id": j.get("job_id", "unknown"), "success": False,
                 "connects_spent": 0, "error": "No valid session"} for j in jobs]

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not headed,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        viewport = session.get("viewport", {"width": 1920, "height": 1080})
        user_agent = session.get("user_agent") or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        context = browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
        )

        # Apply stealth settings
        _apply_stealth(context)

        # Inject cookies
        context.add_cookies(session["cookies"])

        page = context.new_page()

        # Apply stealth to this specific page if plugin is available
        if HAS_STEALTH:
            stealth_sync(page)

        # Verify session health
        print("[applier] Verifying session...")
        if not session_manager.check_session_health(page, session_name):
            print("[applier] Session is invalid. Run login_helper.py to re-authenticate.")
            browser.close()
            return [{"job_id": j.get("job_id", "unknown"), "success": False,
                     "connects_spent": 0, "error": "Session expired"} for j in jobs]

        print(f"[applier] Session valid. Processing {len(jobs)} job(s)...")

        for i, job in enumerate(jobs):
            job_id = job.get("job_id", f"unknown_{i}")
            print(f"\n{'=' * 50}")
            print(f"[applier] Job {i + 1}/{len(jobs)}: {job_id}")
            print(f"{'=' * 50}")

            # Check daily budget
            if tracker:
                budget = tracker.check_daily_budget(daily_limit, daily_budget)
                if not budget["can_apply"]:
                    msg = (
                        f"Daily budget exhausted: "
                        f"{budget['apps_today']}/{daily_limit} apps, "
                        f"{budget['connects_today']}/{daily_budget} connects"
                    )
                    print(f"[applier] {msg}")
                    results.append({
                        "job_id": job_id,
                        "success": False,
                        "connects_spent": 0,
                        "error": msg,
                    })
                    break

            # Determine rate/bid
            hourly_rate = job.get("hourly_rate") or default_rate
            fixed_bid = job.get("fixed_bid")

            # Apply
            apply_result = apply_to_job(
                page=page,
                job_url=job["apply_url"],
                cover_letter=job["cover_letter"],
                hourly_rate=hourly_rate if not fixed_bid else None,
                fixed_bid=fixed_bid,
                skip_boost=skip_boost,
                screenshot_dir=screenshot_dir,
            )

            result = {
                "job_id": job_id,
                "success": apply_result["success"],
                "connects_spent": apply_result.get("connects_spent", 0),
                "error": apply_result.get("error"),
            }
            results.append(result)

            # Update tracker
            if tracker:
                if apply_result["success"]:
                    tracker.update_application_status(
                        job_id=job_id,
                        status="applied",
                        applied_at=datetime.now(timezone.utc).isoformat(),
                    )
                    tracker.update_daily_stats(
                        jobs_applied=1,
                        connects_spent=apply_result.get("connects_spent", 0),
                    )
                else:
                    tracker.update_application_status(
                        job_id=job_id,
                        status="failed",
                        error_message=apply_result.get("error"),
                    )
                    tracker.update_daily_stats(errors=1)

            # Delay between applications (skip after last job)
            if i < len(jobs) - 1:
                delay = random.uniform(delay_min, delay_max)
                print(f"[applier] Waiting {delay:.0f}s before next application...")
                time.sleep(delay)

        browser.close()

    # Summary
    successes = sum(1 for r in results if r["success"])
    total_connects = sum(r.get("connects_spent", 0) for r in results)
    print(f"\n[applier] Batch complete: {successes}/{len(results)} successful, {total_connects} connects spent.")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply to an Upwork job")
    parser.add_argument("--job-url", required=True, help="Upwork job URL")
    parser.add_argument("--cover-letter", required=True, help="Cover letter text")
    parser.add_argument("--rate", type=float, default=None, help="Hourly rate to bid")
    parser.add_argument("--fixed-bid", type=float, default=None, help="Fixed price bid")
    parser.add_argument("--headed", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--screenshot-dir", default=None, help="Directory to save screenshots")
    parser.add_argument("--session", default="default", help="Session name to use")
    args = parser.parse_args()

    # Load config for defaults
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {"auto_apply": {"skip_boost": True, "default_hourly_rate": 75}}

    # Run as single job
    job = {
        "job_id": args.job_url.split("/")[-1] or "cli_job",
        "apply_url": args.job_url,
        "cover_letter": args.cover_letter,
    }
    if args.rate:
        job["hourly_rate"] = args.rate
    if args.fixed_bid:
        job["fixed_bid"] = args.fixed_bid

    results = run_apply_batch(
        jobs=[job],
        config=config,
        session_name=args.session,
        headed=args.headed,
        screenshot_dir=args.screenshot_dir,
    )

    # Exit code based on success
    sys.exit(0 if results and results[0]["success"] else 1)
