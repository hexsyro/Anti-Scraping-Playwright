import random
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext
except ImportError:  # pragma: no cover - allows import without Playwright
    from typing import Any
    sync_playwright = None
    Browser = BrowserContext = Any

from ._compat import require_playwright, safe_print
from .scraper import ProxyServer  # single shared definition

@dataclass
class SessionConfig:
    proxy: ProxyServer
    user_agent: Optional[str] = None
    viewport: Dict = field(default_factory=lambda: {"width": 1920, "height": 1080})
    locale: str = "en-US"
    timezone: str = "America/New_York"
    clear_cookies: bool = True
    clear_cache: bool = True
    clear_storage: bool = True


class CleanSessionManager:
    
    def __init__(self, proxies: List[ProxyServer], user_agents: List[str] = None):
        """
        Initialize the clean session manager.
        
        Args:
            proxies: List of proxy servers
            user_agents: List of user agents (optional)
        """
        if not proxies:
            raise ValueError("proxies must contain at least one ProxyServer")
        self.proxies = list(proxies)
        self.user_agents = user_agents or self._get_default_user_agents()
        self.current_proxy_index = 0
        self.session_count = 0
        self.sessions_history = []
    
    def _get_default_user_agents(self) -> List[str]:
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def get_next_proxy(self) -> ProxyServer:
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self) -> ProxyServer:
        return random.choice(self.proxies)
    
    def create_clean_session(self, browser: Browser, 
                            proxy: ProxyServer = None,
                            user_agent: str = None,
                            **context_options) -> BrowserContext:
        """
        Create a completely clean browser context with new proxy.
        
        Args:
            browser: Playwright browser instance
            proxy: Specific proxy (if None, uses next in rotation)
            user_agent: Specific user agent (if None, uses random)
            **context_options: Additional context options
        
        Returns:
            Fresh BrowserContext with no cookies or cache
        """
        if proxy is None:
            proxy = self.get_next_proxy()
        
        if user_agent is None:
            user_agent = random.choice(self.user_agents)
        
        # Create completely fresh context
        options = {
            "proxy": proxy.to_playwright_format(),
            "user_agent": user_agent,
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "ignore_https_errors": True,
        }
        options.update(context_options)
        context = browser.new_context(**options)
        
        self.session_count += 1
        self.sessions_history.append({
            "session_id": self.session_count,
            "proxy": proxy.server,
            "user_agent": user_agent if len(user_agent) <= 53 else user_agent[:50] + "...",
            "timestamp": datetime.now().isoformat()
        })
        
        safe_print(f"✓ Created clean session #{self.session_count} with proxy: {proxy.server}")
        return context
    
    def clear_context_data(self, context: BrowserContext, config: Optional[SessionConfig] = None):
        """Clear cookies and storage from a context.

        Args:
            context: BrowserContext to clear
            config: Optional SessionConfig controlling which stores are cleared
        """
        clear_cookies = config.clear_cookies if config else True
        clear_cache = config.clear_cache if config else True
        clear_storage = config.clear_storage if config else True

        if clear_cookies:
            context.clear_cookies()
        if not (clear_cache or clear_storage):
            return

        try:
            script = """
                (options) => {
                    if (options.clearStorage) {
                        localStorage.clear();
                        sessionStorage.clear();
                        if (window.indexedDB && window.indexedDB.databases) {
                            window.indexedDB.databases().then(dbs => {
                                dbs.forEach(db => window.indexedDB.deleteDatabase(db.name));
                            });
                        }
                    }
                    if (options.clearCache && window.caches) {
                        caches.keys().then(names => names.forEach(name => caches.delete(name)));
                    }
                }
            """
            for page in context.pages:
                page.evaluate(script, {"clearStorage": clear_storage, "clearCache": clear_cache})
        except Exception as e:
            safe_print(f"Warning: Could not clear all storage: {e}")

    def create_session_from_config(self, browser: Browser, config: SessionConfig,
                                   **context_options) -> BrowserContext:
        """Create a context configured from a :class:`SessionConfig`.

        ``clear_*`` flags are applied when :meth:`clear_context_data` is called
        on the returned context.
        """
        options = {
            "viewport": config.viewport,
            "locale": config.locale,
            "timezone_id": config.timezone,
        }
        options.update(context_options)
        context = self.create_clean_session(
            browser, proxy=config.proxy, user_agent=config.user_agent, **options
        )
        return context
    
    def rotate_session(self, browser: Browser, old_context: BrowserContext = None,
                      **context_options) -> BrowserContext:
        """
        Close old context and create new clean session with different proxy.
        
        Args:
            browser: Playwright browser instance
            old_context: Previous context to close
            **context_options: Additional context options
        
        Returns:
            New clean BrowserContext
        """
        if old_context:
            safe_print("Closing old session...")
            old_context.close()
        
        return self.create_clean_session(browser, **context_options)
    
    def get_session_info(self, context: BrowserContext) -> Dict:
        cookies = context.cookies()
        
        return {
            "cookie_count": len(cookies),
            "cookies": cookies,
            "session_count": self.session_count
        }
    
    def save_cookies(self, context: BrowserContext, filepath: str):
        cookies = context.cookies()
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
        safe_print(f"Saved {len(cookies)} cookies to {filepath}")
    
    def load_cookies(self, context: BrowserContext, filepath: str):
        with open(filepath, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        safe_print(f"Loaded {len(cookies)} cookies from {filepath}")


# Example 1: Basic cookie cleaning with proxy rotation
def example_basic_clean_sessions():
    proxies = [
        ProxyServer("http://proxy1.example.com:8080"),
        ProxyServer("http://proxy2.example.com:8080"),
        ProxyServer("http://proxy3.example.com:8080"),
    ]
    
    manager = CleanSessionManager(proxies)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        urls = [
            "https://httpbin.org/cookies/set?session=abc123",
            "https://httpbin.org/cookies/set?session=xyz789",
            "https://httpbin.org/cookies/set?session=test456",
        ]
        
        for i, url in enumerate(urls):
            safe_print(f"\n{'='*60}")
            safe_print(f"Request {i+1}: Visiting {url}")
            safe_print('='*60)
            
            context = manager.create_clean_session(browser)
            page = context.new_page()
            
            page.goto(url)
            time.sleep(1)
            
            page.goto("https://httpbin.org/cookies")
            safe_print(f"Cookies on page: {page.content()[:200]}")
            
            info = manager.get_session_info(context)
            safe_print(f"Total cookies in context: {info['cookie_count']}")
            
            context.close()
            safe_print("✓ Session closed, cookies cleared")
        
        browser.close()


# Example 2: Manual cookie clearing
def example_manual_cookie_clearing():
    proxies = [ProxyServer("http://proxy1.example.com:8080")]
    manager = CleanSessionManager(proxies)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = manager.create_clean_session(browser)
        page = context.new_page()
        
        safe_print("\n1. Setting cookies...")
        page.goto("https://httpbin.org/cookies/set?test=value1")
        page.goto("https://httpbin.org/cookies")
        safe_print(f"Cookies: {page.text_content('body')[:150]}")
        
        safe_print("\n2. Clearing cookies manually...")
        manager.clear_context_data(context)
        
        safe_print("\n3. Checking cookies after clear...")
        page.goto("https://httpbin.org/cookies")
        safe_print(f"Cookies: {page.text_content('body')[:150]}")
        
        context.close()
        browser.close()


# Example 3: Session rotation during long scraping
def example_session_rotation():
    proxies = [
        ProxyServer("http://proxy1.example.com:8080"),
        ProxyServer("http://proxy2.example.com:8080"),
        ProxyServer("http://proxy3.example.com:8080"),
    ]
    
    manager = CleanSessionManager(proxies)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context = manager.create_clean_session(browser)
        page = context.new_page()
        
        urls = [
            "https://example.com",
            "https://httpbin.org/ip",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/headers",
        ]
        
        for i, url in enumerate(urls):
            safe_print(f"\n{'='*60}")
            safe_print(f"Request {i+1}: {url}")
            
            if i > 0 and i % 2 == 0:
                safe_print("\n🔄 Rotating to new clean session...")
                context = manager.rotate_session(browser, context)
                page = context.new_page()
            
            page.goto(url)
            safe_print(f"✓ Loaded: {page.title()}")
            time.sleep(1)
        
        context.close()
        browser.close()


# Example 4: Cookie persistence (save/load)
def example_cookie_persistence():
    """Example showing how to save and load cookies when needed."""
    proxies = [ProxyServer("http://proxy1.example.com:8080")]
    manager = CleanSessionManager(proxies)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        safe_print("\n=== Session 1: Login ===")
        context1 = manager.create_clean_session(browser)
        page1 = context1.new_page()
        
        page1.goto("https://httpbin.org/cookies/set?session=logged_in_user")
        safe_print("✓ Logged in (cookies set)")
        
        manager.save_cookies(context1, "saved_cookies.json")
        context1.close()
        
        safe_print("\n=== Session 2: Load saved session ===")
        context2 = manager.create_clean_session(browser)
        page2 = context2.new_page()
    
        page2.goto("https://httpbin.org/cookies")
        safe_print("Before loading: No cookies")
        
        manager.load_cookies(context2, "saved_cookies.json")
        
        page2.goto("https://httpbin.org/cookies")
        safe_print(f"After loading: {page2.text_content('body')[:150]}")
        
        context2.close()
        browser.close()


# Example 5: Multi-account with clean sessions
def example_multi_account():
    """Example managing multiple accounts with isolated sessions."""
    proxies = [
        ProxyServer("http://proxy1.example.com:8080"),
        ProxyServer("http://proxy2.example.com:8080"),
        ProxyServer("http://proxy3.example.com:8080"),
    ]
    
    manager = CleanSessionManager(proxies)
    
    accounts = [
        {"username": "user1", "cookies": "user1_cookies.json"},
        {"username": "user2", "cookies": "user2_cookies.json"},
        {"username": "user3", "cookies": "user3_cookies.json"},
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        for account in accounts:
            safe_print(f"\n{'='*60}")
            safe_print(f"Processing account: {account['username']}")
            safe_print('='*60)
            
            context = manager.create_clean_session(browser)
            page = context.new_page()
            
            page.goto(f"https://httpbin.org/cookies/set?user={account['username']}")
            safe_print(f"✓ Logged in as {account['username']}")
            
            page.goto("https://httpbin.org/headers")
            safe_print(f"✓ Fetched data for {account['username']}")
            
            time.sleep(1)
            
            context.close()
            safe_print(f"✓ Session closed for {account['username']}")
        
        browser.close()


# Example 6: Advanced rotation with request tracking
def example_advanced_rotation():
    """Advanced example with request tracking and automatic rotation."""
    proxies = [
        ProxyServer("http://proxy1.example.com:8080"),
        ProxyServer("http://proxy2.example.com:8080"),
    ]
    
    manager = CleanSessionManager(proxies)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context = None
        requests_per_session = 0
        max_requests_per_session = 3
        
        urls = [f"https://httpbin.org/headers?request={i}" for i in range(8)]
        
        for i, url in enumerate(urls):
            if context is None or requests_per_session >= max_requests_per_session:
                safe_print(f"\n{'='*60}")
                safe_print("Creating new clean session (requests limit reached)")
                safe_print('='*60)
                
                context = manager.rotate_session(browser, context)
                page = context.new_page()
                requests_per_session = 0
            
            safe_print(f"\nRequest {i+1}/{len(urls)} (Session request #{requests_per_session + 1})")
            page.goto(url)
            requests_per_session += 1
            
            info = manager.get_session_info(context)
            safe_print(f"Cookies: {info['cookie_count']}, Total sessions: {info['session_count']}")
            
            time.sleep(0.5)
        
        if context:
            context.close()
        browser.close()
        
        safe_print(f"\n{'='*60}")
        safe_print(f"Summary: {len(manager.sessions_history)} total sessions created")
        safe_print('='*60)


if __name__ == "__main__":
    require_playwright()
    safe_print("=" * 60)
    safe_print("Cookie Cleaning with Proxy Rotation Examples")
    safe_print("=" * 60)
    
    # Note: Replace example proxies with real ones to test
    safe_print("\n⚠️  Replace example proxies with real ones before running!")
    safe_print("\nExample 1: Basic Clean Sessions")
    safe_print("-" * 60)
    # example_basic_clean_sessions()
    
    safe_print("\nExample 2: Manual Cookie Clearing")
    safe_print("-" * 60)
    # example_manual_cookie_clearing()
    
    safe_print("\nExample 3: Session Rotation")
    safe_print("-" * 60)
    # example_session_rotation()
    
    safe_print("\nExample 4: Cookie Persistence")
    safe_print("-" * 60)
    # example_cookie_persistence()
    
    safe_print("\nExample 5: Multi-Account Management")
    safe_print("-" * 60)
    # example_multi_account()
    
    safe_print("\nExample 6: Advanced Rotation with Tracking")
    safe_print("-" * 60)
    # example_advanced_rotation()
    
    safe_print("\n✓ Code ready! Uncomment examples to run.")
