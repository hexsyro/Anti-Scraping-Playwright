"""Cross-platform output and public API checks."""

import io

from anti_scraping_playwright._compat import safe_print
from anti_scraping_playwright import (
    CleanSessionManager,
    HoneypotDetector,
    HumanBehavior,
    ProxyServer,
    StealthContext,
    UserAgentRotator,
)


class LegacyStream(io.StringIO):
    encoding = "cp1252"


def test_safe_print_falls_back_to_ascii_on_legacy_encodings():
    stream = LegacyStream()

    safe_print("\u2192 \u2713 done", file=stream)

    assert "-> [OK] done" in stream.getvalue()


def test_public_api_exports_the_toolkit():
    assert all(
        value is not None
        for value in (
            CleanSessionManager,
            HoneypotDetector,
            HumanBehavior,
            ProxyServer,
            StealthContext,
            UserAgentRotator,
        )
    )
