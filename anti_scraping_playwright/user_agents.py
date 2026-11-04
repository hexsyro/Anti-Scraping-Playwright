import random
from playwright.sync_api import sync_playwright, Browser, BrowserContext
from typing import List, Optional

class UserAgentRotator:
    
    def __init__(self, user_agents: Optional[List[str]] = None):
        self.user_agents = user_agents or self._get_default_user_agents()
        self.current_index = 0
    
    def _get_default_user_agents(self) -> List[str]:
        return [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    def get_random(self) -> str:
        return random.choice(self.user_agents)
    
    def get_next(self) -> str:
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua
    
    def create_context(self, browser: Browser, **kwargs) -> BrowserContext:
        ua = self.get_random()
        return browser.new_context(user_agent=ua, **kwargs)


# Example 1: Basic usage with random rotation
def example_random_rotation():
    rotator = UserAgentRotator()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Visit multiple pages with different user agents
        for i in range(3):
            context = rotator.create_context(browser)
            page = context.new_page()
            
            page.goto("https://httpbin.org/headers")
            print(f"Request {i+1} User-Agent:", page.text_content("body"))
            
            context.close()
        
        browser.close()


# Example 2: Sequential rotation
def example_sequential_rotation():
    rotator = UserAgentRotator()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        urls = [
            "https://example.com",
            "https://httpbin.org/user-agent",
            "https://www.whatismybrowser.com"
        ]
        
        for url in urls:
            ua = rotator.get_next()
            context = browser.new_context(user_agent=ua)
            page = context.new_page()
            
            print(f"Visiting {url} with UA: {ua[:50]}...")
            page.goto(url)
            page.wait_for_timeout(2000)
            
            context.close()
        
        browser.close()


# Example 3: Custom user agents
def example_custom_user_agents():
    custom_agents = [
        "Mozilla/5.0 (Custom Agent 1)",
        "Mozilla/5.0 (Custom Agent 2)",
        "Mozilla/5.0 (Custom Agent 3)",
    ]
    
    rotator = UserAgentRotator(user_agents=custom_agents)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        for i in range(5):
            context = rotator.create_context(browser)
            page = context.new_page()
            
            page.goto("https://httpbin.org/user-agent")
            print(f"Request {i+1}:", page.text_content("body"))
            
            context.close()
        
        browser.close()


# Example 4: Async version
async def example_async_rotation():
    from playwright.async_api import async_playwright
    
    rotator = UserAgentRotator()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        for i in range(3):
            ua = rotator.get_random()
            context = await browser.new_context(user_agent=ua)
            page = await context.new_page()
            
            await page.goto("https://httpbin.org/user-agent")
            content = await page.text_content("body")
            print(f"Async request {i+1}:", content)
            
            await context.close()
        
        await browser.close()


if __name__ == "__main__":
    print("Example 1: Random Rotation")
    print("-" * 50)
    example_random_rotation()
    
    print("\n\nExample 2: Sequential Rotation")
    print("-" * 50)
    example_sequential_rotation()
    
    print("\n\nExample 3: Custom User Agents")
    print("-" * 50)
    example_custom_user_agents()
    
    # Uncomment to run async example
    # import asyncio
    # print("\n\nExample 4: Async Rotation")
    # print("-" * 50)
    # asyncio.run(example_async_rotation())