"""Honeypot filtering must work for arbitrary selectors."""

from unittest.mock import Mock, patch

from anti_scraping_playwright.honeypot import HoneypotDetector


def test_get_safe_clickable_elements_filters_by_element_not_selector_string():
    detector = HoneypotDetector()
    safe_one, trap, safe_two = Mock(), Mock(), Mock()
    elements = [safe_one, trap, safe_two]

    page = Mock()
    page.locator.return_value.all.return_value = elements
    detector.detect_all_honeypots = Mock(return_value=[])

    with patch.object(
        detector,
        "is_safe_to_click",
        side_effect=lambda page, element: element is not trap,
    ):
        result = detector.get_safe_clickable_elements(page, "a.titlelink")

    assert result == [safe_one, safe_two]
    page.locator.assert_called_with("a.titlelink")


def test_is_safe_element_alias_delegates_to_is_safe_to_click():
    detector = HoneypotDetector()
    page, element = Mock(), Mock()

    with patch.object(detector, "is_safe_to_click", return_value=True) as check:
        assert detector.is_safe_element(page, element) is True

    check.assert_called_once_with(page, element)
