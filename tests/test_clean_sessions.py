"""Clean-session options can override defaults without launching a browser."""

from unittest.mock import Mock

import pytest

from anti_scraping_playwright.proxy import CleanSessionManager, ProxyServer


@pytest.fixture
def manager():
    return CleanSessionManager(
        [ProxyServer("http://proxy.example:8080")], user_agents=["fixture-agent"]
    )


def test_clean_session_preserves_defaults(manager):
    browser = Mock()

    context = manager.create_clean_session(browser)

    assert context is browser.new_context.return_value
    browser.new_context.assert_called_once_with(
        proxy={"server": "http://proxy.example:8080"},
        user_agent="fixture-agent",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
        ignore_https_errors=True,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"viewport": {"width": 800, "height": 600}},
        {"viewport": None},
        {"locale": "pt-BR", "timezone_id": "America/Sao_Paulo"},
        {"ignore_https_errors": False},
        {"java_script_enabled": False},
    ],
)
def test_clean_session_forwards_context_overrides(manager, overrides):
    browser = Mock()

    manager.create_clean_session(browser, **overrides)

    options = browser.new_context.call_args.kwargs
    assert {key: options[key] for key in overrides} == overrides
    assert options["proxy"] == {"server": "http://proxy.example:8080"}
    assert options["user_agent"] == "fixture-agent"
    assert manager.session_count == 1


def test_rotate_session_forwards_overrides(manager):
    browser, old_context = Mock(), Mock()

    context = manager.rotate_session(browser, old_context, locale="pt-BR")

    old_context.close.assert_called_once_with()
    assert browser.new_context.call_args.kwargs["locale"] == "pt-BR"
    assert context is browser.new_context.return_value
