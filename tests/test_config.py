import pytest

from anti_scraping_playwright.scraper import ScraperConfig


def test_valid_config_defaults():
    cfg = ScraperConfig()
    assert cfg.max_retries == 3
    assert cfg.retry_backoff == 1.5


def test_invalid_browser_type():
    with pytest.raises(ValueError):
        ScraperConfig(browser_type="safari")


def test_invalid_retry_backoff():
    with pytest.raises(ValueError):
        ScraperConfig(retry_backoff=0.5)


def test_invalid_delay_range():
    with pytest.raises(ValueError):
        ScraperConfig(action_delay_range=(2.0, 1.0))