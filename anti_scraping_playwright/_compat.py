"""Cross-platform output helpers and optional-dependency guards."""

from __future__ import annotations

import sys
from typing import Any

# Characters used by the toolkit that are not representable in legacy Windows
# console encodings such as cp1252.
_UNICODE_FALLBACKS = {
    "\u2192": "->",   # arrow used by navigate()
    "\u2713": "[OK]",
    "\u2717": "[X]",
    "\u26a0": "[WARN]",
    "\u2705": "[OK]",
    "\u274c": "[FAIL]",
    "\u2b50": "*",
    "\U0001f504": "[ROTATE]",
    "\U0001f6d1": "[STOP]",
    "\U0001f50d": "[SCAN]",
    "\U0001f517": "[LINK]",
    "\U0001f4c0": "[PAGE]",
    "\U0001f4dd": "[WRITE]",
    "\U0001f44d": "[OK]",
    "\U0001f680": "[GO]",
    "\U0001f389": "[DONE]",
    "\U0001f4a1": "*",
    "\u2500": "-",
    "\u2550": "=",
    "\u2551": "|",
    "\u2554": "+",
    "\u2557": "+",
    "\u255a": "+",
    "\u255d": "+",
    "\u2502": "|",
    "\ufe0f": "",  # variation selector
}


def configure_stdio() -> None:
    """Best-effort UTF-8 reconfiguration of stdout/stderr.

    Some environments (notably Windows consoles using cp1252) cannot encode the
    status glyphs used by this package.  ``safe_print`` handles those cases, but
    reconfiguring also protects user code that prints toolkit messages.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):  # pragma: no cover - exotic streams
            pass


def _ascii_safe(value: Any, encoding: str) -> Any:
    if not isinstance(value, str):
        return value
    try:
        value.encode(encoding)
        return value
    except UnicodeEncodeError:
        pass
    for original, replacement in _UNICODE_FALLBACKS.items():
        value = value.replace(original, replacement)
    return value.encode("ascii", "replace").decode("ascii")


def safe_print(*values: Any, **kwargs: Any) -> None:
    """``print`` that never raises ``UnicodeEncodeError`` on legacy consoles."""
    stream = kwargs.get("file") or sys.stdout
    encoding = getattr(stream, "encoding", None) or "ascii"
    print(*(_ascii_safe(value, encoding) for value in values), **kwargs)


def require_playwright() -> None:
    """Raise an actionable error when the optional Playwright dependency is absent."""
    try:
        import playwright  # noqa: F401
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Playwright is required for browser operations. Install it with "
            "`pip install playwright` and then `python -m playwright install chromium`."
        ) from exc
