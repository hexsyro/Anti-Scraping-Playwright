# Anti-Blocking Web Scraper for Playwright Python

A production-ready, feature-rich web scraping framework that bypasses common anti-bot measures using advanced evasion techniques.

## Features

### 1. **User Agent Rotation**
- Automatic rotation with each session
- 5+ default modern user agents
- Support for custom user agent lists

### 2. **Proxy Rotation**
- Round-robin proxy switching
- Support for HTTP, HTTPS, SOCKS5
- Authenticated proxy support
- **Tor Browser integration**

### 3. **Human-Like Behavior**
- Random delays (configurable ranges)
- Natural typing with realistic typos
- Human-like mouse movements
- Realistic scrolling patterns
- Reading delays based on content length

### 4. **Cookie & Session Management**
- Automatic cookie cleaning
- Fresh session with each proxy rotation
- Configurable requests-per-session limit

### 5. **Honeypot Detection & Evasion**
- Detects invisible elements
- Pattern-based detection (class/id/name)
- Skips trap links automatically
- `safe_click()` and `get_safe_links()` methods

### 6. **Anti-Fingerprinting**
- Canvas fingerprint randomization
- Audio context spoofing
- WebGL parameter masking
- Randomized viewport sizes
- Timezone randomization

### 7. **Stealth Mode**
- Removes `navigator.webdriver`
- Mocks Chrome runtime
- Spoofs plugins & languages
- Removes automation indicators

### 8. **Tor Browser Support**
- Easy Tor integration (`use_tor=True`)
- SOCKS5 proxy configuration
- Works with Tor Browser bundle



## Installation

# Install Playwright
pip install playwright

# Install browsers
playwright install chromium firefox

# For Tor support (optional)
# Install Tor Browser or standalone Tor daemon
# Default ports: 9050 (SOCKS), 9051 (Control)
    
    # User agent
    user_agents=[],                      # Custom user agents (optional)
    rotate_user_agent=True,              # Rotate UA each session
    
    # Human behavior
    typing_speed_range=(50, 150),        # Milliseconds per keystroke
    action_delay_range=(0.5, 2.0),       # Seconds between actions
    reading_delay_range=(1.0, 3.0),      # Reading time in seconds
    enable_human_behavior=True,          # Enable human simulation
    
    # Session management
    requests_per_session=10,             # Requests before rotation
    auto_rotate_session=True,            # Auto-rotate sessions
    clear_cookies=True,                  # Clear cookies on rotation
    
    # Detection evasion
    detect_honeypots=True,               # Enable honeypot detection
    stealth_mode=True,                   # Enable stealth techniques
    randomize_viewport=True,             # Random screen sizes
    randomize_timezone=True,             # Random timezones
    
    # Browser
    headless=False,                      # Headless mode
    browser_type="chromium"              # chromium, firefox, webkit





## Real-World Project Examples

The scraper includes 6 ready-to-use project templates:

### 1. E-commerce Price Monitor
Track product prices across multiple stores

project_1_ecommerce_price_monitor()


### 2. News Aggregator
Collect articles from news sites with honeypot avoidance

project_2_news_aggregator()


### 3. Real Estate Scraper
Extract property listings with details

project_3_real_estate_scraper()


### 4. Form Automation
Auto-fill and submit forms with human behavior

project_4_form_automation()


### 5. Job Board Scraper
Collect job postings from multiple sources

project_5_job_board_scraper()


### 6. Social Media Monitor
Track trends (respecting ToS)

project_6_social_media_monitor()




## Custom Project Template

def your_custom_scraper():
    # Step 1: Configure
    config = ScraperConfig(
        proxies=[ProxyServer("http://proxy:8080")],
        enable_human_behavior=True,
        detect_honeypots=True,
        headless=False
    )
    
    # Step 2: Create scraper
    scraper = AntiBlockingScraper(config)
    
    # Step 3: Define scraping logic
    def extract_data(page, url):
        # Human behavior
        scraper.human_scroll(page, scrolls=2)
        
        # Extract data (adjust selectors for your site)
        title = page.title()
        items = page.locator('.item-class').all()
        
        data = []
        for item in items:
            data.append({
                "text": item.text_content(),
                "url": url
            })
        
        return data
    
    # Step 4: Run scraper
    urls = ['https://example.com/page1', 'https://example.com/page2']
    results = scraper.scrape_with_rotation(urls, extract_data)
    
    # Step 5: Save results
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)




## Important Notes

1. **Legal & Ethical Use**
   - Always respect `robots.txt`
   - Follow website Terms of Service
   - Use appropriate rate limiting
   - Don't overload servers

2. **Proxy Setup**
   - Replace example proxies with real ones
   - Use residential proxies for better success rates
   - Rotate proxies to avoid IP bans

3. **Tor Browser**
   - Ensure Tor is running before enabling `use_tor=True`
   - Default SOCKS5 port: 9050
   - Install: [Tor Project](https://www.torproject.org/)

4. **Testing**
   - Start with `headless=False` to see what's happening
   - Test on 1-2 URLs first
   - Adjust selectors for your target sites

5. **Performance**
   - Human behavior adds delays (realistic but slower)
   - Disable in `ScraperConfig` if speed is critical
   - Balance between stealth and performance



## Troubleshooting

### Common Issues

**Issue: Proxy not working**

# Check proxy format
ProxyServer("http://ip:port")  # HTTP
ProxyServer("https://ip:port") # HTTPS
ProxyServer("socks5://ip:port") # SOCKS5

# With authentication
ProxyServer("http://ip:port", "username", "password")


**Issue: Elements not found**

# Adjust selectors for your target site
page.locator('.your-selector').all()

# Wait for elements
page.wait_for_selector('.your-selector', timeout=5000)


**Issue: Tor not connecting**

# Check if Tor is running
# Linux/Mac: ps aux | grep tor
# Windows: Check Task Manager

# Start Tor daemon
tor




## Success Tips

1. **Use Multiple Proxies** - Rotate through 5-10+ proxies
2. **Adjust Delays** - Match target site's expected behavior
3. **Monitor Rate Limits** - Stay under detection thresholds
4. **Update Selectors** - Websites change, keep selectors current
5. **Test Thoroughly** - Validate on small samples first



## Contributing

This is a template for your projects. Customize and extend as needed!



## License

Use responsibly and ethically. For educational purposes.



##  Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Tor Project](https://www.torproject.org/)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)



**⭐ Star this project if it helps you!**