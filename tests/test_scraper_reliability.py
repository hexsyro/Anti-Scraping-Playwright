"""Regression tests for scraper lifecycle, rotation and stealth behavior."""

from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest

from anti_scraping_playwright.scraper import AntiBlockingScraper, ProxyServer, ScraperConfig


@contextmanager
def _fake_playwright(browser):
    playwright = Mock()
    playwright.chromium.launch.return_value = browser

    @contextmanager
    def fake_sync_playwright():
        yield playwright

    with (
        patch("anti_scraping_playwright.scraper.sync_playwright", fake_sync_playwright),
        patch("anti_scraping_playwright.scraper.require_playwright"),
    ):
        yield browser


def test_navigate_installs_scripts_once_per_context():
    scraper = AntiBlockingScraper(ScraperConfig(enable_human_behavior=False))
    page = Mock()
    page.context = Mock()

    with patch("anti_scraping_playwright.scraper.time.sleep"):
        for _ in range(3):
            scraper.navigate(page, "https://example.com")

    assert page.context.add_init_script.call_count == 2
    assert page.goto.call_count == 3
    assert page.goto.call_args.kwargs["timeout"] == 30000


def test_browser_is_closed_when_context_creation_fails():
    browser = Mock()
    scraper = AntiBlockingScraper(ScraperConfig(enable_human_behavior=False))

    with _fake_playwright(browser):
        with patch.object(scraper, "create_stealth_context", side_effect=RuntimeError("bad proxy")):
            with pytest.raises(RuntimeError, match="bad proxy"):
                scraper.scrape_with_rotation(["https://example.com"], lambda page, url: None)

    browser.close.assert_called_once_with()


def test_failed_proxy_is_not_reused_during_failover():
    first = ProxyServer("http://first:8080")
    second = ProxyServer("http://second:8080")
    scraper = AntiBlockingScraper(
        ScraperConfig(proxies=[first, second], enable_proxy_health=True)
    )

    scraper.record_proxy_result(first, False)

    assert scraper._get_next_proxy() is second
    assert scraper._get_next_proxy(exclude_servers={second.server}).server == first.server


def test_tor_setup_does_not_mutate_caller_config():
    config = ScraperConfig(use_tor=True)

    first = AntiBlockingScraper(config)
    second = AntiBlockingScraper(config)

    assert config.proxies == []
    assert len(first.proxies) == 1
    assert len(second.proxies) == 1


def test_session_rotation_can_preserve_cookies():
    browser = Mock()
    config = ScraperConfig(clear_cookies=False)
    scraper = AntiBlockingScraper(config)
    old_context = Mock()
    old_context.storage_state.return_value = {"cookies": [{"name": "session", "value": "x"}]}

    with patch.object(scraper, "create_stealth_context", return_value=Mock()) as create:
        scraper._rotate_context(browser, old_context)

    old_context.close.assert_called_once_with()
    assert create.call_args.kwargs["storage_state"] == old_context.storage_state.return_value
