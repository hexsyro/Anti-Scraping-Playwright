"""
Complete Anti-Blocking Web Scraper for Playwright Python
Includes: User Agent Rotation, Human Behavior, Proxy Rotation, Cookie Cleaning,
Honeypot Detection, Anti-Fingerprinting, Stealth Mode, Tor Support
"""

import random
import time
import socket
from typing import Any, List, Dict, Optional, Tuple, Callable
try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Locator
except ImportError:  # pragma: no cover - allows config/tests without playwright installed
    sync_playwright = None
    Browser = BrowserContext = Page = Locator = Any
from dataclasses import dataclass, field

from ._compat import require_playwright, safe_print
from ._stealth_scripts import (
    ALL_SCRIPTS,
    ANTI_FINGERPRINT_SCRIPT,
    STEALTH_SCRIPT,
    StealthScriptInstaller,
)
from .honeypot import HoneypotDetector as FullHoneypotDetector

__version__ = "2.0.0"



# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ProxyServer:
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_playwright_format(self) -> Dict:
        proxy_dict = {"server": self.server}
        if self.username and self.password:
            proxy_dict["username"] = self.username
            proxy_dict["password"] = self.password
        return proxy_dict


@dataclass
class ScraperConfig:
    # Proxy settings
    proxies: List[ProxyServer] = field(default_factory=list)
    use_tor: bool = False
    tor_port: int = 9050
    tor_control_port: int = 9051
    tor_renew_on_rotation: bool = False
    
    # User agent rotation
    user_agents: List[str] = field(default_factory=list)
    rotate_user_agent: bool = True
    
    # Human behavior
    typing_speed_range: Tuple[int, int] = (50, 150)
    action_delay_range: Tuple[float, float] = (0.5, 2.0)
    reading_delay_range: Tuple[float, float] = (1.0, 3.0)
    enable_human_behavior: bool = True
    
    # Session management
    requests_per_session: int = 10
    auto_rotate_session: bool = True
    clear_cookies: bool = True
    
    # Honeypot detection
    detect_honeypots: bool = True
    
    # Stealth and anti-fingerprinting
    stealth_mode: bool = True
    randomize_viewport: bool = True
    randomize_timezone: bool = True
    
    # Browser settings
    headless: bool = False
    browser_type: str = "chromium"

    # Reliability
    max_retries: int = 3
    retry_backoff: float = 1.5
    max_retry_backoff: float = 30.0
    navigation_timeout: Optional[int] = 30000
    proxy_failover: bool = True
    proxy_cooldown: float = 5.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_cooldown: float = 30.0

    # Adaptive behavior
    adaptive_delays: bool = True
    enable_proxy_health: bool = True

    def __post_init__(self):
        if self.browser_type not in {"chromium", "firefox", "webkit"}:
            raise ValueError("browser_type must be chromium, firefox, or webkit")
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if self.retry_backoff < 1.0:
            raise ValueError("retry_backoff must be >= 1.0")
        if self.max_retry_backoff < 1.0:
            raise ValueError("max_retry_backoff must be >= 1.0")
        if self.requests_per_session < 1:
            raise ValueError("requests_per_session must be >= 1")
        if self.circuit_breaker_threshold < 1:
            raise ValueError("circuit_breaker_threshold must be >= 1")
        if self.circuit_breaker_cooldown < 0:
            raise ValueError("circuit_breaker_cooldown must be non-negative")
        if self.proxy_cooldown < 0:
            raise ValueError("proxy_cooldown must be non-negative")
        if self.navigation_timeout is not None and self.navigation_timeout < 1:
            raise ValueError("navigation_timeout must be a positive integer or None")
        if self.tor_port < 1 or self.tor_control_port < 1:
            raise ValueError("Tor ports must be positive integers")
        if self.user_agents and not all(self.user_agents):
            raise ValueError("user_agents must not contain empty strings")
        for name in ("typing_speed_range", "action_delay_range", "reading_delay_range"):
            values = getattr(self, name)
            if len(values) != 2:
                raise ValueError(f"{name} must contain exactly two values")
            if not (0 <= values[0] <= values[1]):
                raise ValueError(f"{name} must be ordered and non-negative")



# The full detector lives in honeypot.py; this alias preserves the old import path.
HoneypotDetector = FullHoneypotDetector

class AntiBlockingScraper:
    """High-level scraper combining stealth, rotation, retries and honeypot checks."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.current_proxy_index = 0
        self.request_count = 0
        self.session_count = 0
        self.honeypot_detector = HoneypotDetector() if config.detect_honeypots else None

        # Adaptive reliability state
        self.proxy_health: Dict[str, float] = {}
        self.proxy_cooldown_until: Dict[str, float] = {}
        self.recent_failures = 0

        # Work on copies: reusing a ScraperConfig must not accumulate state.
        self.user_agents = (
            list(config.user_agents) if config.user_agents else self._get_default_user_agents()
        )
        self.proxies: List[ProxyServer] = list(config.proxies)
        self._script_installer = StealthScriptInstaller()
        self.last_proxy: Optional[ProxyServer] = None

        if config.use_tor:
            self._setup_tor_proxy()

    def _get_default_user_agents(self) -> List[str]:
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def _setup_tor_proxy(self):
        tor_proxy = ProxyServer(f"socks5://127.0.0.1:{self.config.tor_port}")
        self.proxies.insert(0, tor_proxy)
        safe_print(f"✓ Tor proxy configured: socks5://127.0.0.1:{self.config.tor_port}")

    def renew_tor_identity(self) -> bool:
        """Request a new Tor circuit via the control port (no extra dependency)."""
        try:
            with socket.create_connection(
                ("127.0.0.1", self.config.tor_control_port), timeout=5
            ) as connection:
                connection.sendall(b"AUTHENTICATE\r\nSIGNAL NEWNYM\r\nQUIT\r\n")
                connection.recv(4096)
            return True
        except OSError as exc:
            safe_print(f"Warning: could not renew Tor identity: {exc}")
            return False

    def _get_next_proxy(self, exclude_servers: Optional[set] = None) -> Optional[ProxyServer]:
        if not self.proxies:
            return None

        excluded = set(exclude_servers or ())
        now = time.monotonic()
        total = len(self.proxies)
        start = self.current_proxy_index % total

        # Keep the cursor anchored to the full list so health changes cannot
        # distort round-robin order, and never pick a proxy we just excluded.
        for offset in range(total):
            index = (start + offset) % total
            proxy = self.proxies[index]
            if proxy.server in excluded:
                continue
            if self.proxy_cooldown_until.get(proxy.server, 0.0) > now:
                continue
            if (
                self.config.enable_proxy_health
                and self.proxy_health.get(proxy.server, 1.0) < 0.5
            ):
                continue
            self.current_proxy_index = (index + 1) % total
            return proxy

        # Everything is cooling down: fall back to the next one rather than
        # stalling the scrape entirely.
        proxy = self.proxies[start]
        self.current_proxy_index = (start + 1) % total
        return proxy

    def record_proxy_result(self, proxy: Optional[ProxyServer], success: bool):
        if not proxy or not self.config.enable_proxy_health:
            return
        score = self.proxy_health.get(proxy.server, 1.0)
        if success:
            score = min(1.0, score + 0.1)
            self.proxy_cooldown_until.pop(proxy.server, None)
        else:
            score = max(0.0, score - 0.5)
            self.proxy_cooldown_until[proxy.server] = (
                time.monotonic() + self.config.proxy_cooldown
            )
        self.proxy_health[proxy.server] = score

    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    def _get_random_viewport(self) -> Dict:
        if not self.config.randomize_viewport:
            return {"width": 1920, "height": 1080}

        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 2560, "height": 1440},
        ]
        return random.choice(viewports)

    def _get_random_timezone(self) -> str:
        if not self.config.randomize_timezone:
            return "America/New_York"

        timezones = [
            "America/New_York", "America/Los_Angeles", "America/Chicago",
            "Europe/London", "Europe/Paris", "Europe/Berlin",
            "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
        ]
        return random.choice(timezones)

    def _apply_stealth_mode(self, page: Page):
        if not self.config.stealth_mode or page is None:
            return
        context = getattr(page, "context", None)
        if context is None:  # e.g. a bare mock/stub page
            page.add_init_script(STEALTH_SCRIPT)
            return
        self._script_installer.install(context, (("stealth", STEALTH_SCRIPT),))

    def _apply_anti_fingerprinting(self, page: Page):
        if not self.config.stealth_mode or page is None:
            return
        context = getattr(page, "context", None)
        if context is None:
            page.add_init_script(ANTI_FINGERPRINT_SCRIPT)
            return
        self._script_installer.install(
            context, (("anti_fingerprinting", ANTI_FINGERPRINT_SCRIPT),)
        )

    def create_stealth_context(
        self,
        browser: Browser,
        exclude_proxy: Optional[ProxyServer] = None,
        **context_options,
    ) -> BrowserContext:
        """Create a fresh stealth context.

        Explicit ``context_options`` override generated defaults, which makes
        it possible to preserve cookies via ``storage_state`` on rotation.
        """
        excluded = {exclude_proxy.server} if exclude_proxy else None
        proxy = self._get_next_proxy(excluded)
        proxy_config = proxy.to_playwright_format() if proxy else None

        options = {
            "viewport": self._get_random_viewport(),
            "locale": "en-US",
            "timezone_id": self._get_random_timezone(),
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "color_scheme": random.choice(["light", "dark"]),
            "ignore_https_errors": True,
        }
        if self.config.rotate_user_agent:
            options["user_agent"] = self._get_random_user_agent()
        if proxy_config:
            options["proxy"] = proxy_config
        options.update(context_options)

        context = browser.new_context(**options)
        if self.config.stealth_mode:
            self._script_installer.install(context, ALL_SCRIPTS)

        self.session_count += 1
        self.last_proxy = proxy
        safe_print(f"✓ Created stealth session #{self.session_count}")
        if proxy:
            safe_print(f"  Proxy: {proxy.server}")

        return context

    def random_delay(self, min_sec: float = None, max_sec: float = None):
        if not self.config.enable_human_behavior:
            return

        min_s = min_sec if min_sec is not None else self.config.action_delay_range[0]
        max_s = max_sec if max_sec is not None else self.config.action_delay_range[1]

        # Adaptive delays increase when recent failures are detected
        if self.config.adaptive_delays and self.recent_failures > 0:
            factor = 1 + (self.recent_failures * 0.25)
            min_s *= factor
            max_s *= factor

        delay = random.uniform(min_s, max_s)
        time.sleep(delay)
    
    def human_type(self, page: Page, selector: str, text: str, mistakes: bool = True):
        if not self.config.enable_human_behavior:
            page.fill(selector, text)
            return
        
        element = page.locator(selector).first
        element.click()
        self.random_delay(0.1, 0.5)

        for i, char in enumerate(text):
            # Occasional typo
            if mistakes and random.random() < 0.05 and i < len(text) - 1:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.press_sequentially(
                    wrong_char, delay=random.randint(*self.config.typing_speed_range)
                )
                time.sleep(random.uniform(0.1, 0.3))
                page.keyboard.press('Backspace')
                time.sleep(random.uniform(0.05, 0.15))

            element.press_sequentially(
                char, delay=random.randint(*self.config.typing_speed_range)
            )
            
            if random.random() < 0.1:
                time.sleep(random.uniform(0.2, 0.8))
    
    def human_click(self, page: Page, selector: str):
        element = page.locator(selector).first

        if self.config.enable_human_behavior:
            box = element.bounding_box()
            if box:
                x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
                y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.05, 0.2))
        
        element.click()
        self.random_delay(0.3, 1.0)
    
    def human_scroll(self, page: Page, scrolls: int = 3):
        if not self.config.enable_human_behavior:
            return
        
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        viewport_height = viewport['height']
        
        for _ in range(scrolls):
            scroll_amount = viewport_height * random.uniform(0.3, 0.8)
            increments = random.randint(5, 10)
            increment_size = scroll_amount / increments
            
            for _ in range(increments):
                page.mouse.wheel(0, increment_size)
                time.sleep(random.uniform(0.02, 0.05))
            
            time.sleep(random.uniform(1.0, 2.5))
    
    def random_mouse_movement(self, page: Page, movements: int = 3):
        if not self.config.enable_human_behavior:
            return
        
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        for _ in range(movements):
            x = random.randint(0, max(0, viewport['width'] - 1))
            y = random.randint(0, max(0, viewport['height'] - 1))
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.5))
    
    def safe_click(self, page: Page, selector: str) -> bool:
        if not self.config.detect_honeypots:
            self.human_click(page, selector)
            return True
        
        element = page.locator(selector).first
        if self.honeypot_detector.is_safe_element(page, element):
            self.human_click(page, selector)
            return True
        else:
            safe_print(f"⚠️  Skipped honeypot element: {selector}")
            return False
    
    def get_safe_links(self, page: Page, selector: str = 'a') -> List[Locator]:
        all_links = page.locator(selector).all()
        
        if not self.config.detect_honeypots:
            return all_links
        
        safe_links = [
            link for link in all_links 
            if self.honeypot_detector.is_safe_element(page, link)
        ]
        
        safe_print(f"✓ Found {len(safe_links)} safe links out of {len(all_links)} total")
        return safe_links
    
    def should_rotate_session(self) -> bool:
        if not self.config.auto_rotate_session:
            return False
        
        self.request_count += 1
        return self.request_count >= self.config.requests_per_session
    
    def navigate(self, page: Page, url: str, wait_for: str = "load"):
        # Scripts are installed once per context by _apply_stealth_mode /
        # _apply_anti_fingerprinting; repeated navigate() calls stay idempotent.
        self._apply_stealth_mode(page)
        self._apply_anti_fingerprinting(page)

        safe_print(f"→ Navigating to: {url}")
        goto_kwargs = {"wait_until": wait_for}
        if self.config.navigation_timeout is not None:
            goto_kwargs["timeout"] = self.config.navigation_timeout
        page.goto(url, **goto_kwargs)

        if self.config.enable_human_behavior:
            time.sleep(random.uniform(*self.config.reading_delay_range))

    def _rotate_context(self, browser: Browser, old_context: Optional[BrowserContext],
                        exclude_proxy: Optional[ProxyServer] = None) -> BrowserContext:
        """Close a context and create a fresh one, optionally preserving cookies."""
        storage_state = None
        if old_context is not None and not self.config.clear_cookies:
            try:
                storage_state = old_context.storage_state()
            except Exception as exc:  # pragma: no cover - browser-specific
                safe_print(f"Warning: could not preserve storage state: {exc}")
        if old_context is not None:
            old_context.close()

        if self.config.use_tor and self.config.tor_renew_on_rotation:
            self.renew_tor_identity()

        options = {"storage_state": storage_state} if storage_state is not None else {}
        return self.create_stealth_context(browser, exclude_proxy=exclude_proxy, **options)

    def scrape_with_rotation(
        self,
        urls: List[str],
        scrape_callback: Callable[[Page, str], Any],
        **browser_options,
    ) -> List[Any]:
        """Scrape URLs with session rotation, retries and proxy failover.

        ``None`` is appended to the result list for URLs that exhaust all
        retries, so the returned list always aligns with ``urls``.
        """
        require_playwright()
        results: List[Any] = []

        with sync_playwright() as p:
            if self.config.browser_type == "firefox":
                browser = p.firefox.launch(headless=self.config.headless, **browser_options)
            elif self.config.browser_type == "webkit":
                browser = p.webkit.launch(headless=self.config.headless, **browser_options)
            else:
                browser = p.chromium.launch(
                    headless=self.config.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                    **browser_options,
                )

            context: Optional[BrowserContext] = None
            page: Optional[Page] = None

            try:
                for i, url in enumerate(urls):
                    safe_print(f"\n{'='*70}")
                    safe_print(f"Request {i+1}/{len(urls)}: {url}")
                    safe_print('='*70)

                    # Circuit breaker: cool down before starting more work.
                    if self.recent_failures >= self.config.circuit_breaker_threshold:
                        safe_print(
                            f"⛔ Circuit breaker open: cooling down for "
                            f"{self.config.circuit_breaker_cooldown}s"
                        )
                        time.sleep(self.config.circuit_breaker_cooldown)
                        self.recent_failures = 0

                    if context is None or self.should_rotate_session():
                        if context is not None:
                            safe_print("🔄 Rotating session...")
                            context = self._rotate_context(browser, context)
                        else:
                            context = self.create_stealth_context(browser)
                        page = context.new_page()
                        self.request_count = 0

                    attempt = 0
                    success = False
                    proxy_used = self.last_proxy
                    while attempt < self.config.max_retries and not success:
                        attempt += 1
                        try:
                            self.navigate(page, url)
                            results.append(scrape_callback(page, url))

                            safe_print(f"✓ Successfully scraped: {url}")
                            success = True
                            self.recent_failures = 0
                            self.record_proxy_result(proxy_used, True)

                        except Exception as exc:
                            safe_print(
                                f"✗ Attempt {attempt}/{self.config.max_retries} "
                                f"failed for {url}: {exc}"
                            )
                            self.recent_failures += 1
                            self.record_proxy_result(proxy_used, False)
                            if attempt < self.config.max_retries:
                                backoff = (
                                    min(
                                        self.config.retry_backoff ** attempt,
                                        self.config.max_retry_backoff,
                                    )
                                    * random.uniform(0.8, 1.2)
                                )
                                safe_print(f"  Retrying in {backoff:.1f}s...")
                                time.sleep(backoff)
                                if self.config.proxy_failover and self.proxies:
                                    safe_print("  Rotating proxy/session...")
                                    context = self._rotate_context(
                                        browser, context, exclude_proxy=proxy_used
                                    )
                                    page = context.new_page()
                                    self.request_count = 0
                                    proxy_used = self.last_proxy
                            else:
                                results.append(None)

                    if i < len(urls) - 1:
                        self.random_delay()
            finally:
                if context is not None:
                    try:
                        context.close()
                    except Exception:  # pragma: no cover - best-effort cleanup
                        pass
                try:
                    browser.close()
                except Exception:  # pragma: no cover - best-effort cleanup
                    pass

        return results


def example_basic_scraping():
    
    # Configure scraper
    config = ScraperConfig(
        proxies=[
            ProxyServer("http://proxy1.example.com:8080"),
            ProxyServer("http://proxy2.example.com:8080"),
        ],
        rotate_user_agent=True,
        enable_human_behavior=True,
        detect_honeypots=True,
        stealth_mode=True,
        requests_per_session=5,
        headless=False
    )
    
    scraper = AntiBlockingScraper(config)
    
    # URLs to scrape
    urls = [
        "https://httpbin.org/headers",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/ip",
    ]
    
    # Define scraping function
    def scrape_page(page: Page, url: str):
        scraper.random_mouse_movement(page)
        
        scraper.human_scroll(page, scrolls=2)
        
        content = page.content()
        safe_print(f"  Page length: {len(content)} bytes")
        
        return {"url": url, "length": len(content)}
    
    scraper.scrape_with_rotation(urls, scrape_page)
    
    safe_print(f"\n{'='*70}")
    safe_print("Scraped pages successfully")
    safe_print('='*70)


def example_with_tor():
    
    config = ScraperConfig(
        use_tor=True,
        tor_port=9050,
        rotate_user_agent=True,
        enable_human_behavior=True,
        stealth_mode=True,
        headless=False
    )
    
    scraper = AntiBlockingScraper(config)
    
    def scrape_page(page: Page, url: str):
        scraper.human_scroll(page, scrolls=1)
        title = page.title()
        safe_print(f"  Title: {title}")
        return {"url": url, "title": title}
    
    urls = ["https://check.torproject.org/"]
    scraper.scrape_with_rotation(urls, scrape_page)


def example_form_submission():
    
    config = ScraperConfig(
        enable_human_behavior=True,
        detect_honeypots=True,
        stealth_mode=True,
        headless=False
    )
    
    scraper = AntiBlockingScraper(config)
    
    def fill_form(page: Page, url: str):
        # Human-like typing
        scraper.human_type(page, "#username", "john_doe", mistakes=True)
        scraper.human_type(page, "#email", "john@example.com", mistakes=True)
        
        # Safe click (avoids honeypots)
        scraper.safe_click(page, "#submit")
        
        return {"status": "submitted"}
    
    urls = ["https://example.com/form"]
    scraper.scrape_with_rotation(urls, fill_form)


def example_advanced_scraping():
    
    config = ScraperConfig(
        proxies=[ProxyServer("http://proxy.example.com:8080")],
        rotate_user_agent=True,
        enable_human_behavior=True,
        detect_honeypots=True,
        stealth_mode=True,
        requests_per_session=3,
        headless=False
    )
    
    scraper = AntiBlockingScraper(config)
    
    def scrape_news(page: Page, url: str):
        # Get safe links only
        safe_links = scraper.get_safe_links(page, 'a.storylink')
        
        articles = []
        for link in safe_links[:5]:
            title = link.text_content()
            href = link.get_attribute('href')
            articles.append({"title": title, "url": href})
            safe_print(f"  Found article: {title}")
        
        return articles
    
    urls = ["https://news.ycombinator.com"]
    scraper.scrape_with_rotation(urls, scrape_news)





if __name__ == "__main__":
    safe_print("="*70)
    safe_print("Anti-Blocking Web Scraper")
    safe_print("="*70)
    
    safe_print("\n  Important Notes:")
    safe_print("  1. Replace example proxies with real ones")
    safe_print("  2. For Tor: Install Tor Browser and ensure it's running")
    safe_print("  3. Respect robots.txt and website terms of service")
    safe_print("  4. Use responsibly and ethically")
    
    safe_print("\n" + "="*70)
    safe_print("Running Example: Basic Scraping")
    safe_print("="*70)
    
    # Uncomment to run examples
    # example_basic_scraping()
    # example_with_tor()
    # example_form_submission()
    # example_advanced_scraping()
    
    safe_print("\n✓ Code ready! Uncomment examples to run.")
