"""
EXERCISE: Build a Hacker News Article Scraper
=============================================

OBJECTIVE:
Scrape the top stories from Hacker News, extract article details,
and save them to a JSON file using all anti-blocking techniques.

WHAT YOU'LL LEARN:
- Configure the anti-blocking scraper
- Use human-like behavior
- Detect and avoid honeypots
- Extract data from real websites
- Handle pagination
- Save results to JSON

TARGET SITE: https://news.ycombinator.com
(This is a safe site to practice on - they allow scraping)

DIFFICULTY: Beginner to Intermediate
TIME: 30-45 minutes

REQUIREMENTS:
- anti_scraping_playwright package (install with `pip install -e .`)
- Playwright installed
"""

from anti_scraping_playwright import AntiBlockingScraper, ScraperConfig
from anti_scraping_playwright._compat import require_playwright, safe_print

from anti_scraping_playwright.scraper import sync_playwright
import json
from datetime import datetime

try:
    from playwright.sync_api import Page
except ImportError:  # pragma: no cover - type hints only
    from typing import Any as Page

# ============================================================================
# STEP 1: CONFIGURATION (⭐ YOUR TASK: Fill in the config)
# ============================================================================

def step1_create_config():
    """
    TODO: Create a ScraperConfig with the following settings:
    - enable_human_behavior: True
    - detect_honeypots: True
    - stealth_mode: True
    - headless: False (so you can see what's happening)
    - requests_per_session: 3
    """
    config = ScraperConfig(
        # TODO: Add your configuration here
        enable_human_behavior=True,
        detect_honeypots=True,
        stealth_mode=True,
        headless=False,
        requests_per_session=3
    )
    return config


# ============================================================================
# STEP 2: BASIC SCRAPING (⭐ YOUR TASK: Complete the function)
# ============================================================================

def step2_scrape_front_page(page: Page, url: str, scraper: AntiBlockingScraper):
    """
    TODO: Scrape the Hacker News front page
    
    Tasks:
    1. Use scraper.human_scroll() to scroll the page (2-3 scrolls)
    2. Use scraper.random_mouse_movement() to move the mouse (2 movements)
    3. Find all article rows (selector: 'tr.athing')
    4. For each article, extract:
       - rank (selector: 'span.rank')
       - title (selector: 'span.titleline > a')
       - url (href from the title link)
    5. Return a list of dictionaries with the data
    
    HINT: Use page.locator().all() to get all elements
    """
    
    safe_print(f"📰 Scraping: {url}")
    
    # TODO: Add human behavior - scroll the page
    scraper.human_scroll(page, scrolls=2)
    
    # TODO: Add human behavior - random mouse movements
    scraper.random_mouse_movement(page, movements=2)
    
    # TODO: Get all article rows
    articles = page.locator('tr.athing').all()
    
    results = []
    
    # TODO: Loop through articles and extract data
    for article in articles[:10]:  # Get first 10 articles
        try:
            # TODO: Extract rank
            rank = article.locator('span.rank').text_content()
            
            # TODO: Extract title and URL
            title_element = article.locator('span.titleline > a').first
            title = title_element.text_content()
            article_url = title_element.get_attribute('href')
            
            # TODO: Store in results
            results.append({
                'rank': rank.strip().replace('.', ''),
                'title': title.strip(),
                'url': article_url,
                'scraped_at': datetime.now().isoformat()
            })
            
            safe_print(f"  ✓ {rank} {title[:50]}...")
            
        except Exception as e:
            safe_print(f"  ✗ Error extracting article: {e}")
            continue
    
    return results


# ============================================================================
# STEP 3: ADVANCED SCRAPING (⭐ YOUR TASK: Complete the function)
# ============================================================================

def step3_scrape_with_metadata(page: Page, url: str, scraper: AntiBlockingScraper):
    """
    TODO: Scrape articles with additional metadata
    
    Tasks:
    1. Do everything from step2
    2. Also extract from the metadata row (next sibling of 'tr.athing'):
       - points (selector: 'span.score')
       - author (selector: 'a.hnuser')
       - time (selector: 'span.age')
       - comments (selector: 'a' containing 'comment')
    3. Use scraper.get_safe_links() to ensure you're not clicking honeypots
    
    HINT: The metadata row is the next sibling after each article row
    """
    
    safe_print(f"📰 Scraping with metadata: {url}")
    
    # Human behavior
    scraper.human_scroll(page, scrolls=3)
    scraper.random_mouse_movement(page, movements=2)
    
    articles = page.locator('tr.athing').all()
    results = []
    
    for i, article in enumerate(articles[:15]):  # Get first 15
        try:
            # Extract basic info
            rank = article.locator('span.rank').text_content()
            title_element = article.locator('span.titleline > a').first
            title = title_element.text_content()
            article_url = title_element.get_attribute('href')
            
            # TODO: Get the metadata row (next sibling). Numeric IDs are not
            # valid CSS identifiers, so use an attribute selector.
            article_id = article.get_attribute('id')
            metadata_row = page.locator(
                f'[id="{article_id}"]'
            ).locator('xpath=following-sibling::tr[1]')
            
            # TODO: Extract points
            points = "N/A"
            try:
                points = metadata_row.locator('span.score').text_content()
            except Exception:
                pass
            
            # TODO: Extract author
            author = "N/A"
            try:
                author = metadata_row.locator('a.hnuser').text_content()
            except Exception:
                pass
            
            # TODO: Extract time
            time_posted = "N/A"
            try:
                time_posted = metadata_row.locator('span.age').get_attribute('title')
            except Exception:
                pass
            
            # TODO: Extract comment count
            comments = "0"
            try:
                comment_link = metadata_row.locator('a:has-text("comment")').first
                comments = comment_link.text_content().split()[0]
            except Exception:
                pass
            
            results.append({
                'rank': rank.strip().replace('.', ''),
                'title': title.strip(),
                'url': article_url,
                'points': points,
                'author': author,
                'time': time_posted,
                'comments': comments,
                'scraped_at': datetime.now().isoformat()
            })
            
            safe_print(f"  ✓ {rank} {title[:40]}... | {points} | by {author}")
            
        except Exception as e:
            safe_print(f"  ✗ Error: {e}")
            continue
    
    return results


# ============================================================================
# STEP 4: PAGINATION (⭐ YOUR TASK: Complete the function)
# ============================================================================

def step4_scrape_multiple_pages(scraper: AntiBlockingScraper, num_pages: int = 3):
    """
    TODO: Scrape multiple pages of Hacker News
    
    Tasks:
    1. Start with page 1: https://news.ycombinator.com/
    2. Scrape articles from page 1
    3. Find the "More" link at the bottom
    4. Use scraper.safe_click() to click it (avoiding honeypots)
    5. Scrape the next page
    6. Repeat for num_pages
    7. Return all results combined
    
    BONUS: Handle the case where "More" link doesn't exist
    """
    
    safe_print(f"🔄 Scraping {num_pages} pages...")
    
    all_results = []
    require_playwright()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=scraper.config.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = scraper.create_stealth_context(browser)
        page = context.new_page()
        
        # Start with the front page
        current_url = "https://news.ycombinator.com/"
        already_navigated = False

        try:
            for page_num in range(1, num_pages + 1):
                safe_print(f"\n{'='*60}")
                safe_print(f"Page {page_num}/{num_pages}")
                safe_print('='*60)
            
                # Clicking "More" already navigated us; avoid a duplicate load.
                if not already_navigated:
                    scraper.navigate(page, current_url)
                already_navigated = False

                # TODO: Scrape the current page
                results = step3_scrape_with_metadata(page, current_url, scraper)
                all_results.extend(results)
            
                # TODO: Find and click the "More" link if not last page
                if page_num < num_pages:
                    try:
                        # Find the "More" link
                        more_link = page.locator('a.morelink').first
                        next_url = more_link.get_attribute('href')
                    
                        safe_print(f"\n🔗 Found 'More' link: {next_url}")
                    
                        # Human-like delay before clicking
                        scraper.random_delay(1.0, 2.0)
                    
                        # TODO: Click using safe_click or navigate directly
                        scraper.safe_click(page, 'a.morelink')
                    
                        # Wait for new page to load
                        page.wait_for_load_state('networkidle')
                    
                        # Update current URL (already loaded, no second goto needed)
                        current_url = page.url
                        already_navigated = True
                    
                    except Exception as e:
                        safe_print(f"  ⚠️ No more pages or error: {e}")
                        break
        
        finally:
            context.close()
            browser.close()
    
    return all_results


# ============================================================================
# STEP 5: CHALLENGE - EXTRACT COMMENTS (⭐⭐ BONUS TASK)
# ============================================================================

def step5_bonus_scrape_comments(scraper: AntiBlockingScraper, article_url: str):
    """
    BONUS CHALLENGE: Click on an article and scrape its comments
    
    Tasks:
    1. Navigate to an article's comment page
    2. Extract all comments with:
       - author
       - text
       - time
       - nested level (indent)
    3. Use human behavior throughout
    4. Avoid any honeypot elements
    
    This is more advanced! Try it after completing steps 1-4.
    """
    
    safe_print(f"💬 Scraping comments from: {article_url}")
    
    # TODO: Implement comment scraping
    # This is a challenge - try to figure it out!
    
    pass


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_exercise():
    """Run the complete exercise."""
    
    safe_print("="*70)
    safe_print("HACKER NEWS SCRAPER EXERCISE")
    safe_print("="*70)
    
    # STEP 1: Create configuration
    safe_print("\n📋 STEP 1: Creating configuration...")
    config = step1_create_config()
    scraper = AntiBlockingScraper(config)
    safe_print("✓ Configuration created")
    
    # STEP 2: Basic scraping
    safe_print("\n📋 STEP 2: Basic scraping...")
    
    def basic_scrape(page, url):
        return step2_scrape_front_page(page, url, scraper)
    
    results_basic = scraper.scrape_with_rotation(
        ["https://news.ycombinator.com/"], basic_scrape
    )[0] or []
    
    safe_print(f"\n✓ Scraped {len(results_basic)} articles (basic)")
    
    # Save basic results
    with open("hn_articles_basic.json", "w") as f:
        json.dump(results_basic, f, indent=2)
    safe_print("✓ Saved to hn_articles_basic.json")
    
    # STEP 3: Advanced scraping
    safe_print("\n📋 STEP 3: Advanced scraping with metadata...")
    
    def advanced_scrape(page, url):
        return step3_scrape_with_metadata(page, url, scraper)
    
    results_advanced = scraper.scrape_with_rotation(
        ["https://news.ycombinator.com/"], advanced_scrape
    )[0] or []
    
    safe_print(f"\n✓ Scraped {len(results_advanced)} articles (advanced)")
    
    # Save advanced results
    with open("hn_articles_advanced.json", "w") as f:
        json.dump(results_advanced, f, indent=2)
    safe_print("✓ Saved to hn_articles_advanced.json")
    
    # STEP 4: Multiple pages
    safe_print("\n📋 STEP 4: Scraping multiple pages...")
    results_multi = step4_scrape_multiple_pages(scraper, num_pages=2)
    
    safe_print(f"\n✓ Scraped {len(results_multi)} articles from multiple pages")
    
    # Save multi-page results
    with open("hn_articles_multi_page.json", "w") as f:
        json.dump(results_multi, f, indent=2)
    safe_print("✓ Saved to hn_articles_multi_page.json")
    
    # Summary
    safe_print("\n" + "="*70)
    safe_print("EXERCISE COMPLETE! 🎉")
    safe_print("="*70)
    safe_print(f"""
Summary:
- Basic scraping: {len(results_basic)} articles
- Advanced scraping: {len(results_advanced)} articles  
- Multi-page scraping: {len(results_multi)} articles

Files created:
- hn_articles_basic.json
- hn_articles_advanced.json
- hn_articles_multi_page.json

Next Steps:
1. Review the JSON files to see what you scraped
2. Try the bonus challenge (step5_bonus_scrape_comments)
3. Modify the code to scrape other websites
4. Experiment with different configuration options
5. Add proxy support for better anonymity

Great job! 🚀
    """)


# ============================================================================
# EXERCISE VALIDATOR
# ============================================================================

def validate_exercise():
    """Check if the exercise was completed correctly."""
    
    safe_print("\n🔍 VALIDATING YOUR SOLUTION...\n")
    
    errors = []
    warnings = []
    
    # Check if files were created
    import os
    
    required_files = [
        "hn_articles_basic.json",
        "hn_articles_advanced.json", 
        "hn_articles_multi_page.json"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            errors.append(f"Missing file: {file}")
        else:
            # Check if file has content
            with open(file, 'r') as f:
                data = json.load(f)
                if len(data) == 0:
                    warnings.append(f"{file} is empty")
                else:
                    safe_print(f"✓ {file}: {len(data)} articles")
    
    # Check required fields
    try:
        with open("hn_articles_advanced.json", 'r') as f:
            data = json.load(f)
            if data:
                first_article = data[0]
                required_fields = ['rank', 'title', 'url', 'points', 'author', 'comments']
                for field in required_fields:
                    if field not in first_article:
                        errors.append(f"Missing field: {field}")
                    else:
                        safe_print(f"✓ Field '{field}' present")
    except Exception as e:
        errors.append(f"Error validating advanced scraping: {e}")
    
    # Print results
    safe_print("\n" + "="*70)
    if errors:
        safe_print("❌ VALIDATION FAILED")
        for error in errors:
            safe_print(f"  ✗ {error}")
    else:
        safe_print("✅ VALIDATION PASSED!")
    
    if warnings:
        safe_print("\n⚠️  WARNINGS:")
        for warning in warnings:
            safe_print(f"  • {warning}")
    
    safe_print("="*70)


# ============================================================================
# RUN THE EXERCISE
# ============================================================================

if __name__ == "__main__":
    # Import required
    from playwright.sync_api import sync_playwright
    
    safe_print("""
╔════════════════════════════════════════════════════════════════════╗
║                  HACKER NEWS SCRAPER EXERCISE                      ║
╚════════════════════════════════════════════════════════════════════╝

Welcome! This exercise will teach you how to use the anti-blocking
web scraper by building a real Hacker News article scraper.

BEFORE YOU START:
1. Install the package: pip install -e .
2. Install Playwright: pip install playwright
3. Install browsers: playwright install chromium

STEPS:
1. Review the TODO comments in each function
2. Complete the missing code
3. Run: python examples/exercise.py
4. Check the generated JSON files

Ready? Let's begin!
    """)
    
    input("\nPress ENTER to start the exercise...")
    
    try:
        # Run the exercise
        run_exercise()
        
        # Validate results
        validate_exercise()
        
    except KeyboardInterrupt:
        safe_print("\n\n⚠️  Exercise interrupted by user")
    except Exception as e:
        safe_print(f"\n\n❌ Error running exercise: {e}")
        safe_print("\nTIP: Install the package with `pip install -e .` first")
        import traceback
        traceback.print_exc()
    
    safe_print("\n👋 Exercise complete! Happy scraping!")