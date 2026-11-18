"""Quick anti-fingerprinting smoke test against a bot-detection page."""

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - allows import without Playwright
    from typing import Any
    sync_playwright = Any

import random

from ._compat import require_playwright
from ._stealth_scripts import ALL_SCRIPTS, StealthScriptInstaller

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


def run(wait_for_input: bool = False):
    """Launch a stealth browser and visit a fingerprint test page.

    Args:
        wait_for_input: Only prompt when a human explicitly asks to inspect the
            browser.  Automated callers no longer block forever.
    """
    require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1366, "height": 768},
                device_scale_factor=1,
                locale="en-US",
                timezone_id="Asia/Colombo",
                color_scheme="dark",
                java_script_enabled=True,
            )
            StealthScriptInstaller().install(context, ALL_SCRIPTS)
            page = context.new_page()
            page.goto("https://bot.sannysoft.com")
            if wait_for_input:
                input("Press Enter to close...")
        finally:
            browser.close()


if __name__ == "__main__":
    run(wait_for_input=True)
