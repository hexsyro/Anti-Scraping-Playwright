import re
from typing import List, Optional, Tuple
from playwright.sync_api import Page, Locator, ElementHandle
from dataclasses import dataclass
import json

@dataclass
class HoneypotElement:
    selector: str
    element_type: str  # 'link', 'input', 'button', etc.
    reason: str  # Why it's considered a honeypot
    visibility_score: float  # 0 (invisible) to 1 (fully visible)
    text: Optional[str] = None


class HoneypotDetector:
    
    def __init__(self):
        # Common honeypot patterns
        self.honeypot_patterns = {
            'class': [
                r'honeypot', r'hp-field', r'trap', r'bot-trap', r'anti-bot',
                r'hidden-field', r'invisible', r'display-none', r'screen-reader',
                r'visually-hidden', r'sr-only', r'off-screen', r'robot-trap'
            ],
            'id': [
                r'honeypot', r'hp', r'trap', r'bot-field', r'anti-spam',
                r'hidden', r'invisible', r'fake-field', r'decoy'
            ],
            'name': [
                r'honeypot', r'hp', r'email_confirm', r'website', r'url',
                r'phone_confirm', r'trap', r'bot-field'
            ],
            'aria-hidden': [r'true'],
            'data-honeypot': [r'.*']
        }
        
        # Suspicious link text patterns
        self.suspicious_link_text = [
            r'click.*here.*admin', r'hidden.*link', r'bot.*trap',
            r'do.*not.*click', r'invisible', r'test.*link',
            r'crawler.*trap', r'spider.*trap'
        ]
        
        self.detected_honeypots: List[HoneypotElement] = []
    
    def is_invisible_element(self, page: Page, element: ElementHandle) -> Tuple[bool, float]:
        """
        Check if element is invisible using multiple methods.
        
        Returns:
            Tuple of (is_invisible: bool, visibility_score: float)
            visibility_score: 0 = completely invisible, 1 = fully visible
        """
        try:
            # Get computed styles and properties
            visibility_info = page.evaluate("""
                (element) => {
                    const styles = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    
                    return {
                        // CSS visibility
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: parseFloat(styles.opacity),
                        
                        // Position
                        position: styles.position,
                        left: parseInt(styles.left),
                        top: parseInt(styles.top),
                        
                        // Size
                        width: rect.width,
                        height: rect.height,
                        
                        // Z-index
                        zIndex: styles.zIndex,
                        
                        // Clip and overflow
                        clip: styles.clip,
                        clipPath: styles.clipPath,
                        overflow: styles.overflow,
                        
                        // Attributes
                        ariaHidden: element.getAttribute('aria-hidden'),
                        hidden: element.hasAttribute('hidden'),
                        
                        // Position relative to viewport
                        isInViewport: rect.top >= 0 && rect.left >= 0 &&
                                     rect.bottom <= window.innerHeight &&
                                     rect.right <= window.innerWidth
                    };
                }
            """, element)
            
            visibility_score = 1.0
            reasons = []
            
            if visibility_info['display'] == 'none':
                visibility_score = 0
                reasons.append("display: none")
            
            if visibility_info['visibility'] == 'hidden':
                visibility_score = 0
                reasons.append("visibility: hidden")
            
            if visibility_info['opacity'] < 0.1:
                visibility_score *= visibility_info['opacity'] * 10
                reasons.append(f"opacity: {visibility_info['opacity']}")
            
            if visibility_info['position'] in ['absolute', 'fixed']:
                if visibility_info['left'] < -9000 or visibility_info['top'] < -9000:
                    visibility_score = 0
                    reasons.append("positioned off-screen")
            
            if visibility_info['width'] < 1 or visibility_info['height'] < 1:
                visibility_score = 0
                reasons.append("zero/tiny dimensions")
            
            if visibility_info['ariaHidden'] == 'true':
                visibility_score *= 0.5
                reasons.append("aria-hidden=true")
            
            if visibility_info['hidden']:
                visibility_score = 0
                reasons.append("hidden attribute")
            
            if visibility_info['clip'] != 'auto' and 'rect(0' in str(visibility_info['clip']):
                visibility_score = 0
                reasons.append("clipped to zero")
            
            is_invisible = visibility_score < 0.3
            
            return is_invisible, visibility_score
            
        except Exception:
            # If we can't determine, assume visible to be safe
            return False, 1.0
    
    def check_honeypot_patterns(self, element: ElementHandle) -> Tuple[bool, List[str]]:
        """
        Check if element matches common honeypot patterns.
        
        Returns:
            Tuple of (is_honeypot: bool, reasons: List[str])
        """
        try:
            attrs = element.evaluate("""
                (el) => ({
                    className: el.className,
                    id: el.id,
                    name: el.name,
                    type: el.type,
                    tagName: el.tagName.toLowerCase(),
                    ariaHidden: el.getAttribute('aria-hidden'),
                    dataHoneypot: el.getAttribute('data-honeypot'),
                    placeholder: el.placeholder,
                    tabIndex: el.tabIndex
                })
            """)
            
            reasons = []
            
            for attr_name, patterns in self.honeypot_patterns.items():
                attr_value = attrs.get(attr_name.replace('-', ''), '')
                if attr_value:
                    for pattern in patterns:
                        if re.search(pattern, str(attr_value), re.IGNORECASE):
                            reasons.append(f"{attr_name} matches '{pattern}'")
            
            if attrs.get('tabIndex', 0) < 0:
                reasons.append("negative tabIndex (not keyboard accessible)")
            
            if attrs.get('tagName') == 'input':
                name = attrs.get('name', '').lower()
                if any(x in name for x in ['confirm', 'check', 'verify', 'url', 'website']):
                    if attrs.get('type') in ['email', 'url', 'text']:
                        reasons.append("suspicious confirmation field")
            
            is_honeypot = len(reasons) > 0
            return is_honeypot, reasons
            
        except Exception:
            return False, []
    
    def detect_honeypot_links(self, page: Page) -> List[HoneypotElement]:
        honeypots = []
        
        try:
            links = page.locator('a').all()
            
            for i, link in enumerate(links):
                try:
                    is_invisible, visibility_score = self.is_invisible_element(page, link.element_handle())
                    
                    matches_pattern, pattern_reasons = self.check_honeypot_patterns(link.element_handle())
                    
                    text = link.text_content() or ''
                    has_suspicious_text = any(
                        re.search(pattern, text, re.IGNORECASE) 
                        for pattern in self.suspicious_link_text
                    )
                    
                    reasons = []
                    if is_invisible:
                        reasons.append(f"invisible (score: {visibility_score:.2f})")
                    if matches_pattern:
                        reasons.extend(pattern_reasons)
                    if has_suspicious_text:
                        reasons.append(f"suspicious text: '{text}'")
                    
                    if reasons:
                        href = link.get_attribute('href') or ''
                        honeypots.append(HoneypotElement(
                            selector=f"a:nth-of-type({i+1})",
                            element_type='link',
                            reason='; '.join(reasons),
                            visibility_score=visibility_score,
                            text=text[:50]
                        ))
                
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Error detecting honeypot links: {e}")
        
        return honeypots
    
    def detect_honeypot_inputs(self, page: Page) -> List[HoneypotElement]:
        honeypots = []
        
        try:
            inputs = page.locator('input, textarea').all()
            
            for i, input_field in enumerate(inputs):
                try:
                    is_invisible, visibility_score = self.is_invisible_element(page, input_field.element_handle())
                    
                    matches_pattern, pattern_reasons = self.check_honeypot_patterns(input_field.element_handle())
                    
                    reasons = []
                    if is_invisible:
                        reasons.append(f"invisible (score: {visibility_score:.2f})")
                    if matches_pattern:
                        reasons.extend(pattern_reasons)
                    
                    if reasons:
                        name = input_field.get_attribute('name') or ''
                        input_type = input_field.get_attribute('type') or 'text'
                        
                        honeypots.append(HoneypotElement(
                            selector=f"input:nth-of-type({i+1})",
                            element_type=f'input[{input_type}]',
                            reason='; '.join(reasons),
                            visibility_score=visibility_score,
                            text=name
                        ))
                
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Error detecting honeypot inputs: {e}")
        
        return honeypots
    
    def detect_all_honeypots(self, page: Page) -> List[HoneypotElement]:
        self.detected_honeypots = []
        
        link_honeypots = self.detect_honeypot_links(page)
        self.detected_honeypots.extend(link_honeypots)

        input_honeypots = self.detect_honeypot_inputs(page)
        self.detected_honeypots.extend(input_honeypots)
        
        return self.detected_honeypots
    
    def get_safe_clickable_elements(self, page: Page, selector: str = 'a') -> List[Locator]:
        """
        Get only safe (non-honeypot) clickable elements.
        
        Args:
            page: Playwright page
            selector: Element selector (default: 'a' for links)
        
        Returns:
            List of safe Locator objects
        """
        self.detect_all_honeypots(page)
        
        all_elements = page.locator(selector).all()
        
        safe_elements = []
        honeypot_indices = set()
        
        for hp in self.detected_honeypots:
            if selector in hp.selector:
                # Extract index from selector like "a:nth-of-type(5)"
                match = re.search(r'nth-of-type\((\d+)\)', hp.selector)
                if match:
                    honeypot_indices.add(int(match.group(1)) - 1)  # Convert to 0-based
        
        for i, element in enumerate(all_elements):
            if i not in honeypot_indices:
                safe_elements.append(element)
        
        return safe_elements
    
    def is_safe_to_click(self, page: Page, element: Locator) -> bool:
        """
        Check if a specific element is safe to click.
        
        Args:
            page: Playwright page
            element: Element to check
        
        Returns:
            True if safe to click, False if it's a honeypot
        """
        try:
            element_handle = element.element_handle()
            
            is_invisible, visibility_score = self.is_invisible_element(page, element_handle)
            if is_invisible:
                return False
            
            matches_pattern, _ = self.check_honeypot_patterns(element_handle)
            if matches_pattern:
                return False
            
            if element.evaluate("el => el.tagName.toLowerCase()") == 'a':
                text = element.text_content() or ''
                has_suspicious_text = any(
                    re.search(pattern, text, re.IGNORECASE) 
                    for pattern in self.suspicious_link_text
                )
                if has_suspicious_text:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def print_report(self):
        if not self.detected_honeypots:
            print("✓ No honeypots detected!")
            return
        
        print(f"\n⚠️  Detected {len(self.detected_honeypots)} honeypot elements:")
        print("=" * 80)
        
        for i, hp in enumerate(self.detected_honeypots, 1):
            print(f"\n{i}. {hp.element_type.upper()}")
            print(f"   Selector: {hp.selector}")
            print(f"   Visibility Score: {hp.visibility_score:.2f}")
            print(f"   Reason: {hp.reason}")
            if hp.text:
                print(f"   Text/Name: {hp.text}")
        
        print("\n" + "=" * 80)
    
    def save_report(self, filepath: str):
        report = {
            'total_honeypots': len(self.detected_honeypots),
            'honeypots': [
                {
                    'selector': hp.selector,
                    'type': hp.element_type,
                    'reason': hp.reason,
                    'visibility_score': hp.visibility_score,
                    'text': hp.text
                }
                for hp in self.detected_honeypots
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to {filepath}")


# Example 1: Detect honeypots on a page
def example_detect_honeypots():
    """Basic honeypot detection example."""
    from playwright.sync_api import sync_playwright
    
    detector = HoneypotDetector()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.set_content("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .hidden { display: none; }
                .invisible { opacity: 0; }
                .off-screen { position: absolute; left: -9999px; }
            </style>
        </head>
        <body>
            <h1>Test Page</h1>
            
            <!-- Normal links -->
            <a href="/page1">Visible Link 1</a>
            <a href="/page2">Visible Link 2</a>
            
            <!-- Honeypot links -->
            <a href="/admin" class="hidden">Admin Link (display:none)</a>
            <a href="/trap" class="invisible">Trap Link (opacity:0)</a>
            <a href="/bot-trap" class="off-screen">Bot Trap (off-screen)</a>
            <a href="/secret" style="width: 0; height: 0;">Zero Size Link</a>
            
            <!-- Normal form -->
            <form>
                <input type="text" name="username" placeholder="Username">
                <input type="email" name="email" placeholder="Email">
                
                <!-- Honeypot fields -->
                <input type="text" name="honeypot" class="hidden">
                <input type="text" name="website" style="display: none;">
                <input type="email" name="email_confirm" class="off-screen">
            </form>
        </body>
        </html>
        """)
        
        print("\n🔍 Scanning page for honeypots...")
        honeypots = detector.detect_all_honeypots(page)
        
        detector.print_report()
        detector.save_report("honeypot_report.json")
        
        browser.close()


# Example 2: Safe link clicking
def example_safe_link_clicking():
    """Example showing how to click only safe links."""
    from playwright.sync_api import sync_playwright
    
    detector = HoneypotDetector()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.set_content("""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Link Test Page</h1>
            <a href="#safe1">Safe Link 1</a>
            <a href="#safe2">Safe Link 2</a>
            <a href="#trap" class="honeypot" style="display:none;">Hidden Trap</a>
            <a href="#safe3">Safe Link 3</a>
            <a href="#admin" style="opacity: 0;">Invisible Admin</a>
        </body>
        </html>
        """)
        
        print("\n🔍 Getting safe clickable links...")
        safe_links = detector.get_safe_clickable_elements(page, 'a')
        
        print(f"✓ Found {len(safe_links)} safe links out of {len(page.locator('a').all())} total")
        
        print("\n📋 Safe links:")
        for i, link in enumerate(safe_links, 1):
            text = link.text_content()
            print(f"  {i}. {text}")
        
        print("\n🖱️  Clicking safe links only...")
        for link in safe_links:
            text = link.text_content()
            print(f"  Clicking: {text}")
            link.click()
            page.wait_for_timeout(500)
        
        detector.print_report()
        
        browser.close()


# Example 3: Form filling with honeypot avoidance
def example_safe_form_filling():
    """Example showing how to fill forms while avoiding honeypot fields."""
    from playwright.sync_api import sync_playwright
    
    detector = HoneypotDetector()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.set_content("""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Registration Form</h1>
            <form>
                <!-- Real fields -->
                <label>Name: <input type="text" name="name"></label><br>
                <label>Email: <input type="email" name="email"></label><br>
                <label>Phone: <input type="tel" name="phone"></label><br>
                
                <!-- Honeypot fields (hidden from users) -->
                <input type="text" name="website" style="display: none;">
                <input type="text" name="honeypot" class="hp-field" style="position: absolute; left: -9999px;">
                <input type="email" name="email_confirm" style="opacity: 0; height: 0;">
                
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
        """)
        
        print("\n🔍 Detecting honeypot fields...")
        honeypots = detector.detect_all_honeypots(page)
        detector.print_report()
        
        all_inputs = page.locator('input[type="text"], input[type="email"], input[type="tel"]').all()
        
        print("\n📝 Filling only safe fields...")
        for input_field in all_inputs:
            if detector.is_safe_to_click(page, input_field):
                name = input_field.get_attribute('name')
                print(f"  ✓ Filling field: {name}")
                
                if name == 'name':
                    input_field.fill("John Doe")
                elif name == 'email':
                    input_field.fill("john@example.com")
                elif name == 'phone':
                    input_field.fill("123-456-7890")
            else:
                name = input_field.get_attribute('name')
                print(f"  ⚠️  Skipping honeypot field: {name}")
        
        page.wait_for_timeout(2000)
        browser.close()


# Example 4: Real-world scraping with honeypot avoidance
def example_real_world_scraping():
    """Example of scraping a real website while avoiding honeypots."""
    from playwright.sync_api import sync_playwright
    import time
    
    detector = HoneypotDetector()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("\n🌐 Loading Hacker News...")
        page.goto("https://news.ycombinator.com")
        
        print("\n🔍 Scanning for honeypots...")
        honeypots = detector.detect_all_honeypots(page)
        
        if honeypots:
            detector.print_report()
        else:
            print("✓ No honeypots detected on this page")
        
        print("\n🔗 Extracting safe article links...")
        safe_links = detector.get_safe_clickable_elements(page, 'a.titlelink')
        
        print(f"✓ Found {len(safe_links)} safe article links")
        
        if safe_links:
            first_safe_link = safe_links[0]
            title = first_safe_link.text_content()
            print(f"\n🖱️  Clicking safe link: {title}")
            first_safe_link.click()
            
            time.sleep(2)
        
        browser.close()


if __name__ == "__main__":
    print("=" * 80)
    print("Honeypot Detection and Evasion Examples")
    print("=" * 80)
    
    print("\nExample 1: Detect Honeypots")
    print("-" * 80)
    example_detect_honeypots()
    
    print("\n\nExample 2: Safe Link Clicking")
    print("-" * 80)
    example_safe_link_clicking()
    
    print("\n\nExample 3: Safe Form Filling")
    print("-" * 80)
    example_safe_form_filling()
    
    print("\n\nExample 4: Real-World Scraping")
    print("-" * 80)
    example_real_world_scraping()