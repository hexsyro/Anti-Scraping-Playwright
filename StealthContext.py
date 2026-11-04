import random
from playwright.sync_api import sync_playwright


class StealthContext:
    """
    Reusable Playwright stealth context
    """

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

    def launch(self):
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

        self.browser = self.playwright.chromium.launch(**launch_args)

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

        if self.user_data_dir:
            self.context = self.browser.new_context(**context_args)
        else:
            self.context = self.browser.new_context(**context_args)

        self._apply_stealth_scripts()

        self.page = self.context.new_page()
        return self.page

    def _apply_stealth_scripts(self):
        self.context.add_init_script("""
        // webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // chrome runtime
        window.chrome = {
            runtime: {}
        };

        // permissions fix
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);
        """)

    def save_storage(self, path: str = "auth.json"):
        self.context.storage_state(path=path)

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
