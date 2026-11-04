"""Anti-Scraping Playwright toolkit."""

__version__ = "2.0.0"

from .anti_block_scraper import AntiBlockingScraper, ScraperConfig, ProxyServer

__all__ = ["AntiBlockingScraper", "ScraperConfig", "ProxyServer", "__version__"]