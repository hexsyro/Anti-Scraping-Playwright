"""Anti-Scraping Playwright toolkit."""

from ._compat import configure_stdio

configure_stdio()

from .behavior import HumanBehavior  # noqa: E402
from .fingerprint import run as run_fingerprint_check  # noqa: E402
from .honeypot import HoneypotDetector, HoneypotElement  # noqa: E402
from .mouse import (  # noqa: E402
    bezier_curve,
    ease_in_out,
    human_click,
    human_mouse_move,
    move_to_element,
)
from .proxy import CleanSessionManager, SessionConfig  # noqa: E402
from .scraper import AntiBlockingScraper, ProxyServer, ScraperConfig  # noqa: E402
from .stealth import StealthContext  # noqa: E402
from .user_agents import UserAgentRotator  # noqa: E402

__version__ = "2.0.0"
__all__ = [
    "AntiBlockingScraper",
    "ScraperConfig",
    "ProxyServer",
    "CleanSessionManager",
    "SessionConfig",
    "HumanBehavior",
    "StealthContext",
    "HoneypotDetector",
    "HoneypotElement",
    "UserAgentRotator",
    "human_mouse_move",
    "human_click",
    "move_to_element",
    "ease_in_out",
    "bezier_curve",
    "run_fingerprint_check",
    "__version__",
]
