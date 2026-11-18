import random

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - allows import without Playwright
    from typing import Any
    sync_playwright = Any

from ._compat import require_playwright
from ._stealth_scripts import ALL_SCRIPTS, StealthScriptInstaller


class StealthContext:
    """Reusable Playwright stealth context."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        headless: bool = False,
        proxy: dict | None = None,
        user_data_dir: str | None = None,
        storage_state: str | None = None,
    ):
        self.headless = headless
        self.proxy = proxy
        self.user_data_dir = user_data_dir
        self.storage_state = storage_state

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._script_installer = StealthScriptInstaller()

    def launch(self):
        require_playwright()
        self.playwright = sync_playwright().start()

        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        }
        if self.proxy:
            launch_args["proxy"] = self.proxy

        context_args = {
            "user_agent": random.choice(self.USER_AGENTS),
            "viewport": {"width": 1366, "height": 768},
            "device_scale_factor": 1,
            "locale": "en-US",
            "timezone_id": "Asia/Colombo",
            "java_script_enabled": True,
        }
        if self.storage_state:
            context_args["storage_state"] = self.storage_state

        try:
            if self.user_data_dir:
                # A persistent profile is owned by the context, not by a
                # separately launched browser.
                self.context = self.playwright.chromium.launch_persistent_context(
                    self.user_data_dir, **launch_args, **context_args
                )
                self.browser = None
            else:
                self.browser = self.playwright.chromium.launch(**launch_args)
                self.context = self.browser.new_context(**context_args)

            self._apply_stealth_scripts()
            self.page = self.context.new_page()
            return self.page
        except Exception:
            # Never leak the Playwright driver if setup fails.
            self.close()
            raise

    def _apply_stealth_scripts(self):
        self._script_installer.install(self.context, ALL_SCRIPTS)

    def save_storage(self, path: str = "auth.json"):
        if self.context is None:
            raise RuntimeError("launch() must be called before save_storage()")
        self.context.storage_state(path=path)

    def close(self):
        try:
            if self.context is not None:
                self.context.close()
        finally:
            try:
                if self.browser is not None:
                    self.browser.close()
            finally:
                if self.playwright is not None:
                    self.playwright.stop()
                self.context = None
                self.browser = None
                self.page = None
                self.playwright = None
