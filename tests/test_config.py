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


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typing_speed_range": (150, 50)},
        {"requests_per_session": 0},
        {"circuit_breaker_threshold": 0},
        {"circuit_breaker_cooldown": -1},
        {"proxy_cooldown": -1},
        {"navigation_timeout": 0},
    ],
)
def test_invalid_numeric_options(kwargs):
    with pytest.raises(ValueError):
        ScraperConfig(**kwargs)


def test_empty_proxy_manager_is_rejected():
    from anti_scraping_playwright.proxy import CleanSessionManager

    with pytest.raises(ValueError):
        CleanSessionManager([])