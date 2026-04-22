"""
Complete Anti-Blocking Web Scraper for Playwright Python
Includes: User Agent Rotation, Human Behavior, Proxy Rotation, Cookie Cleaning,
Honeypot Detection, Anti-Fingerprinting, Stealth Mode, Tor Support
"""

import random
import time
import re
from typing import List, Dict, Optional, Tuple, Callable
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Locator
from dataclasses import dataclass, field



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



class HoneypotDetector:
    
    def __init__(self):
        self.honeypot_patterns = {
            'class': [r'honeypot', r'hp-field', r'trap', r'bot-trap', r'hidden-field', 
                     r'invisible', r'display-none', r'screen-reader', r'off-screen'],
            'id': [r'honeypot', r'hp', r'trap', r'bot-field', r'hidden', r'invisible'],
            'name': [r'honeypot', r'hp', r'email_confirm', r'website', r'url', r'trap'],
        }
        self.detected_honeypots = []
    
    def is_invisible_element(self, page: Page, element) -> Tuple[bool, float]:
        try:
            visibility_info = page.evaluate("""
                (element) => {
                    const styles = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: parseFloat(styles.opacity),
                        position: styles.position,
                        left: parseInt(styles.left),
                        top: parseInt(styles.top),
                        width: rect.width,
                        height: rect.height,
                        ariaHidden: element.getAttribute('aria-hidden'),
                        hidden: element.hasAttribute('hidden')
                    };
                }
            """, element)
            
            visibility_score = 1.0
            
            if visibility_info['display'] == 'none':
                visibility_score = 0
            if visibility_info['visibility'] == 'hidden':
                visibility_score = 0
            if visibility_info['opacity'] < 0.1:
                visibility_score *= visibility_info['opacity'] * 10
            if visibility_info['position'] in ['absolute', 'fixed']:
                if visibility_info['left'] < -9000 or visibility_info['top'] < -9000:
                    visibility_score = 0
            if visibility_info['width'] < 1 or visibility_info['height'] < 1:
                visibility_score = 0
            if visibility_info['ariaHidden'] == 'true':
                visibility_score *= 0.5
            if visibility_info['hidden']:
                visibility_score = 0
            
            return visibility_score < 0.3, visibility_score
        except:
            return False, 1.0
    
    def check_honeypot_patterns(self, element) -> bool:
        try:
            attrs = element.evaluate("""
                (el) => ({
                    className: el.className || '',
                    id: el.id || '',
                    name: el.name || ''
                })
            """)
            
            for attr_name, patterns in self.honeypot_patterns.items():
                attr_value = attrs.get(attr_name, '')
                for pattern in patterns:
                    if re.search(pattern, str(attr_value), re.IGNORECASE):
                        return True
            return False
        except:
            return False
    
    def is_safe_element(self, page: Page, element: Locator) -> bool:
        try:
            element_handle = element.element_handle()
            is_invisible, _ = self.is_invisible_element(page, element_handle)
            if is_invisible:
                return False
            matches_pattern = self.check_honeypot_patterns(element_handle)
            return not matches_pattern
        except:
            return False




class AntiBlockingScraper:
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.current_proxy_index = 0
        self.request_count = 0
        self.session_count = 0
        self.honeypot_detector = HoneypotDetector() if config.detect_honeypots else None
        
        if not self.config.user_agents:
            self.config.user_agents = self._get_default_user_agents()
        
        if self.config.use_tor:
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
        self.config.proxies.insert(0, tor_proxy)
        print(f"✓ Tor proxy configured: socks5://127.0.0.1:{self.config.tor_port}")
    
    def _get_next_proxy(self) -> Optional[ProxyServer]:
        if not self.config.proxies:
            return None
        proxy = self.config.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.config.proxies)
        return proxy
    
    def _get_random_user_agent(self) -> str:
        return random.choice(self.config.user_agents)
    
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
        if not self.config.stealth_mode:
            return
        
        # Inject stealth scripts
        page.add_init_script("""
            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Overwrite the `languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Overwrite the `webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Mock chrome object
            window.chrome = {
                runtime: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Remove automation indicators
            delete navigator.__proto__.webdriver;
        """)
    
    def _apply_anti_fingerprinting(self, page: Page):
        if not self.config.stealth_mode:
            return
        
        page.add_init_script("""
            // Randomize canvas fingerprinting
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                }
                context.putImageData(imageData, 0, 0);
                return originalToDataURL.apply(this, arguments);
            };
            
            // Randomize audio fingerprinting
            const audioContext = window.AudioContext || window.webkitAudioContext;
            if (audioContext) {
                const originalCreateAnalyser = audioContext.prototype.createAnalyser;
                audioContext.prototype.createAnalyser = function() {
                    const analyser = originalCreateAnalyser.call(this);
                    const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                    analyser.getFloatFrequencyData = function(array) {
                        originalGetFloatFrequencyData.call(this, array);
                        for (let i = 0; i < array.length; i++) {
                            array[i] += Math.random() * 0.1 - 0.05;
                        }
                    };
                    return analyser;
                };
            }
            
            // Randomize WebGL fingerprinting
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };
        """)
    
    def create_stealth_context(self, browser: Browser) -> BrowserContext:
        # Get next proxy if available
        proxy = self._get_next_proxy()
        proxy_config = proxy.to_playwright_format() if proxy else None
        
        # Create context options
        context_options = {
            "viewport": self._get_random_viewport(),
            "locale": "en-US",
            "timezone_id": self._get_random_timezone(),
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "color_scheme": random.choice(["light", "dark"]),
            "ignore_https_errors": True,
        }
        
        # Add user agent
        if self.config.rotate_user_agent:
            context_options["user_agent"] = self._get_random_user_agent()
        
        # Add proxy
        if proxy_config:
            context_options["proxy"] = proxy_config
        
        # Create context
        context = browser.new_context(**context_options)
        
        self.session_count += 1
        print(f"✓ Created stealth session #{self.session_count}")
        if proxy:
            print(f"  Proxy: {proxy.server}")
        
        return context
    
    def random_delay(self, min_sec: float = None, max_sec: float = None):
        if not self.config.enable_human_behavior:
            return
        
        min_s = min_sec if min_sec is not None else self.config.action_delay_range[0]
        max_s = max_sec if max_sec is not None else self.config.action_delay_range[1]
        delay = random.uniform(min_s, max_s)
        time.sleep(delay)
    
    def human_type(self, page: Page, selector: str, text: str, mistakes: bool = True):
        if not self.config.enable_human_behavior:
            page.fill(selector, text)
            return
        
        element = page.locator(selector)
        element.click()
        self.random_delay(0.1, 0.5)
        
        for i, char in enumerate(text):
            # Occasional typo
            if mistakes and random.random() < 0.05 and i < len(text) - 1:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.type(wrong_char, delay=random.randint(*self.config.typing_speed_range))
                time.sleep(random.uniform(0.1, 0.3))
                page.keyboard.press('Backspace')
                time.sleep(random.uniform(0.05, 0.15))
            
            element.type(char, delay=random.randint(*self.config.typing_speed_range))
            
            if random.random() < 0.1:
                time.sleep(random.uniform(0.2, 0.8))
    
    def human_click(self, page: Page, selector: str):
        element = page.locator(selector)
        
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
        
        viewport_height = page.viewport_size['height']
        
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
        
        viewport = page.viewport_size
        for _ in range(movements):
            x = random.randint(0, viewport['width'])
            y = random.randint(0, viewport['height'])
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
            print(f"⚠️  Skipped honeypot element: {selector}")
            return False
    
    def get_safe_links(self, page: Page, selector: str = 'a') -> List[Locator]:
        all_links = page.locator(selector).all()
        
        if not self.config.detect_honeypots:
            return all_links
        
        safe_links = [
            link for link in all_links 
            if self.honeypot_detector.is_safe_element(page, link)
        ]
        
        print(f"✓ Found {len(safe_links)} safe links out of {len(all_links)} total")
        return safe_links
    
    def should_rotate_session(self) -> bool:
        if not self.config.auto_rotate_session:
            return False
        
        self.request_count += 1
        return self.request_count >= self.config.requests_per_session
    
    def navigate(self, page: Page, url: str, wait_for: str = "load"):
        print(f"→ Navigating to: {url}")
        page.goto(url, wait_until=wait_for)
        
        # Apply stealth and anti-fingerprinting
        self._apply_stealth_mode(page)
        self._apply_anti_fingerprinting(page)
        
        # Random initial delay (reading page)
        if self.config.enable_human_behavior:
            time.sleep(random.uniform(*self.config.reading_delay_range))
    
    def scrape_with_rotation(self, 
                            urls: List[str], 
                            scrape_callback: Callable[[Page, str], any],
                            **browser_options) -> List[any]:
        """
        Scrape multiple URLs with automatic session rotation.
        
        Args:
            urls: List of URLs to scrape
            scrape_callback: Function(page, url) that performs scraping
            **browser_options: Additional browser launch options
        
        Returns:
            List of results from scrape_callback
        """
        results = []
        
        with sync_playwright() as p:
            # Launch browser
            if self.config.browser_type == "firefox":
                browser = p.firefox.launch(headless=self.config.headless, **browser_options)
            elif self.config.browser_type == "webkit":
                browser = p.webkit.launch(headless=self.config.headless, **browser_options)
            else:
                browser = p.chromium.launch(
                    headless=self.config.headless,
                    args=['--disable-blink-features=AutomationControlled'],
                    **browser_options
                )
            
            context = None
            page = None
            
            for i, url in enumerate(urls):
                print(f"\n{'='*70}")
                print(f"Request {i+1}/{len(urls)}: {url}")
                print('='*70)
                
                # Create new session if needed
                if context is None or self.should_rotate_session():
                    if context:
                        print("🔄 Rotating session...")
                        context.close()
                    
                    context = self.create_stealth_context(browser)
                    page = context.new_page()
                    self.request_count = 0
                
                try:
                    # Navigate to URL
                    self.navigate(page, url)
                    
                    # Execute scraping callback
                    result = scrape_callback(page, url)
                    results.append(result)
                    
                    print(f"✓ Successfully scraped: {url}")
                    
                except Exception as e:
                    print(f"✗ Error scraping {url}: {e}")
                    results.append(None)
                
                # Random delay between requests
                if i < len(urls) - 1:
                    self.random_delay()
            
            # Cleanup
            if context:
                context.close()
            browser.close()
        
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
        print(f"  Page length: {len(content)} bytes")
        
        return {"url": url, "length": len(content)}
    
    results = scraper.scrape_with_rotation(urls, scrape_page)
    
    print(f"\n{'='*70}")
    print(f"Scraped {len(results)} pages successfully")
    print('='*70)


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
        print(f"  Title: {title}")
        return {"url": url, "title": title}
    
    urls = ["https://check.torproject.org/"]
    results = scraper.scrape_with_rotation(urls, scrape_page)


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
    results = scraper.scrape_with_rotation(urls, fill_form)


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
            print(f"  Found article: {title}")
        
        return articles
    
    urls = ["https://news.ycombinator.com"]
    results = scraper.scrape_with_rotation(urls, scrape_news)





if __name__ == "__main__":
    print("="*70)
    print("Anti-Blocking Web Scraper")
    print("="*70)
    
    print("\n  Important Notes:")
    print("  1. Replace example proxies with real ones")
    print("  2. For Tor: Install Tor Browser and ensure it's running")
    print("  3. Respect robots.txt and website terms of service")
    print("  4. Use responsibly and ethically")
    
    print("\n" + "="*70)
    print("Running Example: Basic Scraping")
    print("="*70)
    
    # Uncomment to run examples
    # example_basic_scraping()
    # example_with_tor()
    # example_form_submission()
    # example_advanced_scraping()
    
    print("\n✓ Code ready! Uncomment examples to run.")
