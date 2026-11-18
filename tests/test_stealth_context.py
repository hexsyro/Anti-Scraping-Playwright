"""StealthContext must honour user_data_dir and clean up on failures."""

from contextlib import contextmanager
from unittest.mock import Mock, patch

from anti_scraping_playwright.stealth import StealthContext


@contextmanager
def _patch_driver():
    playwright = Mock()
    driver = Mock()
    driver.start.return_value = playwright

    with (
        patch("anti_scraping_playwright.stealth.sync_playwright", Mock(return_value=driver)),
        patch("anti_scraping_playwright.stealth.require_playwright"),
    ):
        yield playwright


def test_user_data_dir_uses_persistent_context():
    with _patch_driver() as playwright:
        stealth = StealthContext(user_data_dir="/tmp/profile")
        stealth.launch()

    playwright.chromium.launch_persistent_context.assert_called_once()
    playwright.chromium.launch.assert_not_called()
    playwright.chromium.launch.return_value.new_context.assert_not_called()
    stealth.close()


def test_launch_cleans_up_driver_on_failure():
    with _patch_driver() as playwright:
        playwright.chromium.launch.side_effect = RuntimeError("launch failed")
        stealth = StealthContext()

        try:
            stealth.launch()
        except RuntimeError:
            pass

    playwright.stop.assert_called_once()
