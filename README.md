# Anti-Scraping Playwright

![Anti-Scraping Playwright](docs/banner.png)

A production-ready Python toolkit for building resilient web scrapers with Playwright. It combines stealth browser contexts, human-like interaction, proxy rotation, honeypot evasion, and anti-fingerprinting techniques to help automate data collection responsibly.

## Features

- **User Agent Rotation** — Round-robin and random selection from a curated list of modern user agents.
- **Proxy Rotation** — HTTP, HTTPS, and SOCKS5 proxies with authentication and Tor support.
- **Human-Like Behavior** — Randomized delays, natural typing with typos, Bezier mouse movement, and realistic scrolling.
- **Honeypot Detection** — Identifies invisible and pattern-matched trap elements and skips them automatically.
- **Anti-Fingerprinting** — Canvas, audio, and WebGL fingerprint randomization plus viewport and timezone spoofing.
- **Stealth Mode** — Removes automation indicators such as `navigator.webdriver` and mocks Chrome runtime.
- **Session Management** — Cookie clearing, storage cleanup, and automatic session rotation.
- **Reliability** — Retry logic with exponential backoff, proxy health scoring, circuit breaker, and adaptive delays.

## Installation

```bash
pip install -e .
playwright install chromium firefox
```

Optional dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from anti_scraping_playwright import AntiBlockingScraper, ScraperConfig

config = ScraperConfig(
    enable_human_behavior=True,
    detect_honeypots=True,
    stealth_mode=True,
    headless=False,
    requests_per_session=5,
)

scraper = AntiBlockingScraper(config)

def extract(page, url):
    scraper.human_scroll(page, scrolls=2)
    return {"title": page.title(), "url": url}

results = scraper.scrape_with_rotation(
    ["https://example.com"],
    extract,
)
print(results)
```

## Configuration

`ScraperConfig` accepts the following options:

| Option | Type | Default | Description |
|---|---|---|---|
| `proxies` | `list[ProxyServer]` | `[]` | Proxy servers to rotate through |
| `use_tor` | `bool` | `False` | Enable Tor SOCKS5 proxy |
| `tor_port` | `int` | `9050` | Tor SOCKS port |
| `user_agents` | `list[str]` | built-in | Custom user agent list |
| `rotate_user_agent` | `bool` | `True` | Rotate user agent per session |
| `typing_speed_range` | `tuple[int,int]` | `(50,150)` | Keystroke delay in ms |
| `action_delay_range` | `tuple[float,float]` | `(0.5,2.0)` | Delay between actions (s) |
| `reading_delay_range` | `tuple[float,float]` | `(1.0,3.0)` | Reading delay (s) |
| `enable_human_behavior` | `bool` | `True` | Enable human simulation |
| `requests_per_session` | `int` | `10` | Requests before session rotation |
| `auto_rotate_session` | `bool` | `True` | Rotate sessions automatically |
| `clear_cookies` | `bool` | `True` | Clear cookies on rotation |
| `detect_honeypots` | `bool` | `True` | Enable honeypot detection |
| `stealth_mode` | `bool` | `True` | Enable stealth techniques |
| `randomize_viewport` | `bool` | `True` | Randomize viewport sizes |
| `randomize_timezone` | `bool` | `True` | Randomize timezones |
| `headless` | `bool` | `False` | Headless browser mode |
| `browser_type` | `str` | `"chromium"` | `chromium`, `firefox`, or `webkit` |
| `max_retries` | `int` | `3` | Retry attempts per URL |
| `retry_backoff` | `float` | `1.5` | Exponential backoff base |
| `proxy_failover` | `bool` | `True` | Rotate proxy on failure |
| `circuit_breaker_threshold` | `int` | `5` | Consecutive failures before cooldown |
| `circuit_breaker_cooldown` | `float` | `30.0` | Cooldown duration (s) |
| `adaptive_delays` | `bool` | `True` | Increase delays after failures |
| `enable_proxy_health` | `bool` | `True` | Track and prefer healthy proxies |

## Project Structure

```
anti_scraping_playwright/   # Python package
├── scraper.py
├── proxy.py
├── stealth.py
├── honeypot.py
├── behavior.py
├── fingerprint.py
├── user_agents.py
└── mouse.py
examples/
└── exercise.py
tests/
└── test_config.py
docs/
```

## Running Tests

Run the full workflow test suite (the same checks executed by the GitHub Actions
`CI` workflow on every pull request) before opening a PR:

```bash
make workflow
```

Or run the individual checks:

```bash
python -m pytest -q
python -m ruff check .
python -m compileall anti_scraping_playwright tests examples
```

The `CI` workflow (`.github/workflows/ci.yml`) runs these checks across Python
3.10–3.13 on every pull request, so running them locally first helps identify
bugs before review.

## Examples

See `examples/exercise.py` for a guided Hacker News scraping exercise demonstrating configuration, human behavior, honeypot avoidance, pagination, and JSON export.

## Responsible Use

This toolkit is intended for educational and authorized automation. Always respect `robots.txt`, website Terms of Service, and applicable laws. Do not use it to overload servers or collect data you are not permitted to access.

## Contributing

Contributions are welcome. Please open an issue or pull request. Follow PEP 8, add docstrings, and include tests for new behavior.

## License

Released under the MIT License. See `LICENSE` for details.

## Resources

- [Playwright for Python](https://playwright.dev/python/)
- [Tor Project](https://www.torproject.org/)