"""Anti-Scraping Playwright toolkit."""

from .scraper import AntiBlockingScraper, ScraperConfig, ProxyServer

__version__ = "2.0.0"
__all__ = ["AntiBlockingScraper", "ScraperConfig", "ProxyServer", "__version__"]