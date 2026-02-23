#!/usr/bin/env python3
"""
One-time local script to capture Upwork session cookies.

Opens a headed (visible) Playwright Chromium browser, navigates to the Upwork
login page, waits for the user to log in manually, then captures cookies and
stores them via session_manager.save_session().

Usage:
    python login_helper.py
    python login_helper.py --session-name my_account
"""

import argparse
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(
        "ERROR: Playwright is not installed.\n"
        "Install it with:  pip install playwright && playwright install chromium"
    )
    sys.exit(1)

from session_manager import save_session


def capture_upwork_session(session_name: str = "default"):
    """Open a headed browser, let user log in to Upwork, capture cookies."""

    print("=" * 60)
    print("  Upwork Session Capture")
    print("=" * 60)
    print()
    print("A browser window will open to the Upwork login page.")
    print("Log in with your Upwork credentials (including any 2FA).")
    print("Once you see your Upwork dashboard, come back here and press Enter.")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        # Navigate to login
        print("[*] Opening Upwork login page...")
        page.goto(
            "https://www.upwork.com/ab/account-security/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        # Wait for user to finish logging in
        input("\n>>> Log in to Upwork in the browser, then press Enter here... ")

        # Give page a moment to settle after any final redirects
        page.wait_for_timeout(2000)

        # Capture cookies
        cookies = context.cookies()
        if not cookies:
            print("[!] WARNING: No cookies captured. Login may not have completed.")
            browser.close()
            return

        # Get user agent from the browser
        user_agent = page.evaluate("() => navigator.userAgent")

        # Save to Supabase
        print(f"[*] Captured {len(cookies)} cookies. Saving to Supabase...")
        success = save_session(
            cookies=cookies,
            user_agent=user_agent,
            session_name=session_name,
        )

        if success:
            print(f"[+] Session '{session_name}' saved successfully!")
            print(f"    Cookies: {len(cookies)}")
            print(f"    User-Agent: {user_agent[:80]}...")
        else:
            print("[!] Failed to save session to Supabase. Check your credentials.")

        browser.close()

    print("\nDone. You can now use applier.py with this session.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture Upwork login session cookies")
    parser.add_argument(
        "--session-name",
        default="default",
        help="Name for this session (default: 'default')",
    )
    args = parser.parse_args()
    capture_upwork_session(session_name=args.session_name)
