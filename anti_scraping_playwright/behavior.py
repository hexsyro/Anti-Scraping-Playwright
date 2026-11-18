import random
import time
from typing import Tuple

try:
    from playwright.sync_api import Page
except ImportError:  # pragma: no cover - allows import without Playwright
    from typing import Any
    Page = Any

from ._compat import safe_print

class HumanBehavior:
    
    def __init__(self, 
                 typing_speed_range: Tuple[int, int] = (50, 150),
                 action_delay_range: Tuple[float, float] = (0.5, 2.0),
                 read_delay_range: Tuple[float, float] = (1.0, 3.0)):
        self.typing_speed_range = typing_speed_range
        self.action_delay_range = action_delay_range
        self.read_delay_range = read_delay_range
    
    def random_delay(self, min_sec: float = None, max_sec: float = None):
        min_s = min_sec if min_sec is not None else self.action_delay_range[0]
        max_s = max_sec if max_sec is not None else self.action_delay_range[1]
        delay = random.uniform(min_s, max_s)
        time.sleep(delay)
    
    def reading_delay(self, text_length: int = 100):
        words = text_length / 5
        base_time = words / 4
        delay = base_time * random.uniform(0.7, 1.3)
        delay = max(self.read_delay_range[0], min(delay, self.read_delay_range[1] * 2))
        time.sleep(delay)
    
    def human_type(self, page: Page, selector: str, text: str, mistakes: bool = True):
        element = page.locator(selector).first
        element.click()

        self.random_delay(0.1, 0.5)

        for i, char in enumerate(text):
            if mistakes and random.random() < 0.05 and i < len(text) - 1:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.press_sequentially(wrong_char, delay=random.randint(*self.typing_speed_range))
                time.sleep(random.uniform(0.1, 0.3))
                page.keyboard.press('Backspace')
                time.sleep(random.uniform(0.05, 0.15))

            element.press_sequentially(char, delay=random.randint(*self.typing_speed_range))

            if random.random() < 0.1:
                time.sleep(random.uniform(0.2, 0.8))

    def human_click(self, page: Page, selector: str):
        element = page.locator(selector).first

        box = element.bounding_box()
        if box:
            x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
            y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
            page.mouse.move(x, y)
            
            time.sleep(random.uniform(0.05, 0.2))
        
        element.click()
        self.random_delay(0.3, 1.0)
    
    def human_scroll(self, page: Page, scrolls: int = 3):
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        viewport_height = viewport['height']
        
        for _ in range(scrolls):
            scroll_amount = viewport_height * random.uniform(0.3, 0.8)
            
            increments = random.randint(5, 10)
            increment_size = scroll_amount / increments
            
            for _ in range(increments):
                page.mouse.wheel(0, increment_size)
                time.sleep(random.uniform(0.02, 0.05))
            
            self.reading_delay(random.randint(50, 200))
    
    def random_mouse_movement(self, page: Page, movements: int = 3):
        viewport = page.viewport_size or {"width": 1280, "height": 720}

        for _ in range(movements):
            x = random.randint(0, max(0, viewport['width'] - 1))
            y = random.randint(0, max(0, viewport['height'] - 1))
            
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.5))
    
    def hover_element(self, page: Page, selector: str):
        element = page.locator(selector).first
        box = element.bounding_box()
        
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.2, 0.8))


# Example 1: Form filling with human behavior
def example_form_filling():
    from playwright.sync_api import sync_playwright
    
    human = HumanBehavior()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        safe_print("Navigating to form...")
        page.goto("https://www.example.com/form")  # Replace with actual form URL
        
        human.reading_delay(100)
        
        human.random_mouse_movement(page, 2)
        
        safe_print("Filling name field...")
        human.human_type(page, "#name", "John Doe", mistakes=True)
        
        safe_print("Filling email field...")
        human.human_type(page, "#email", "john.doe@example.com", mistakes=True)
        
        human.random_delay(1.0, 2.0)
        
        safe_print("Clicking submit...")
        human.human_click(page, "#submit")
        
        page.wait_for_timeout(3000)
        
        browser.close()


# Example 2: Natural page browsing
def example_browsing():
    from playwright.sync_api import sync_playwright
    
    human = HumanBehavior()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        safe_print("Loading page...")
        page.goto("https://news.ycombinator.com")
        
        safe_print("Reading page...")
        human.reading_delay(200)
        
        safe_print("Scrolling...")
        human.human_scroll(page, scrolls=4)
        
        safe_print("Moving mouse naturally...")
        human.random_mouse_movement(page, 3)
        
        links = page.locator("a.titlelink").all()[:5]
        for i, link in enumerate(links):
            safe_print(f"Hovering link {i+1}...")
            box = link.bounding_box()
            if box:
                page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                time.sleep(random.uniform(0.3, 1.0))
        
        if links:
            safe_print("Clicking random article...")
            random_link = random.choice(links[:5])
            human.human_click(page, f"text={random_link.text_content()}")
            
            human.reading_delay(300)
        
        browser.close()


# Example 3: Search behavior
def example_search():
    """Simulate human search behavior."""
    from playwright.sync_api import sync_playwright
    
    human = HumanBehavior()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        safe_print("Going to search engine...")
        page.goto("https://www.google.com")
        
        try:
            page.click("button:has-text('Accept')", timeout=2000)
            human.random_delay(0.5, 1.0)
        except Exception:
            pass
        
        human.reading_delay(50)
        
        safe_print("Typing search query...")
        human.human_type(page, "textarea[name='q']", "playwright automation", mistakes=True)
        
        safe_print("Submitting search...")
        page.keyboard.press("Enter")
        
        page.wait_for_load_state("networkidle")
        human.reading_delay(100)
        
        safe_print("Browsing results...")
        human.human_scroll(page, scrolls=3)
        
        results = page.locator("h3").all()
        if results:
            safe_print("Clicking a result...")
            human.human_click(page, f"h3 >> nth={random.randint(0, min(3, len(results)-1))}")
            
            human.reading_delay(250)
        
        browser.close()


# Example 4: Shopping behavior
def example_shopping():
    """Simulate shopping/product browsing behavior."""
    from playwright.sync_api import sync_playwright
    
    human = HumanBehavior()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        safe_print("Loading e-commerce site...")
        page.goto("https://www.example-shop.com")  # Replace with actual site
        
        safe_print("Looking at products...")
        human.reading_delay(150)
        human.human_scroll(page, scrolls=2)
        
        safe_print("Hovering over products...")
        human.random_mouse_movement(page, 4)
        
        safe_print("Clicking product...")
        # This would be replaced with actual product selectors
        # human.human_click(page, ".product-card >> nth=0")
        
        human.reading_delay(200)
        human.human_scroll(page, scrolls=2)
        
        safe_print("Going back...")
        page.go_back()
        human.random_delay(1.0, 2.0)
        
        browser.close()


if __name__ == "__main__":
    safe_print("=" * 60)
    safe_print("Human Behavior Simulation Examples")
    safe_print("=" * 60)
    
    # Uncomment to run examples
    # safe_print("\n1. Form Filling Example")
    # example_form_filling()
    
    safe_print("\n2. Browsing Example")
    example_browsing()
    
    # safe_print("\n3. Search Example")
    # example_search()
    
    # safe_print("\n4. Shopping Example")
    # example_shopping()