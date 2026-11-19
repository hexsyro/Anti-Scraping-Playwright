# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Fixed
- `examples/exercise.py` now calls the real `scrape_with_rotation()` API instead of
  the non-existent `scrape_single()`; numeric Hacker News IDs use an attribute
  selector, pagination no longer navigates twice, and browser cleanup is in a
  `finally` block.
- Stealth and anti-fingerprinting init scripts are installed once per browser
  context instead of on every navigation, preventing duplicate-script errors and
  fingerprint inconsistencies. Scripts are also safe on tainted/WebGL canvases,
  WebGL2, and preserve an existing `window.chrome` object.
- Honeypot filtering now checks each matched element directly, so it works with
  qualified selectors such as `a.titlelink`; pattern checks no longer flag every
  non-focusable element or ordinary `url`/`website` field names.
- `StealthContext(user_data_dir=...)` now uses `launch_persistent_context()` so
  profiles actually persist; failed launches no longer leak the driver.
- `safe_click()`, `human_click()`, `human_type()` and behavior helpers resolve a
  single element with `.first` and use the non-deprecated `press_sequentially()`.
- Proxy health/cooldown/failover no longer reuse failing proxies or drift their
  round-robin cursor, and all-unhealthy pools no longer silently retry dead hosts.
- `ScraperConfig` construction no longer mutates the caller's proxy/user-agent
  lists; Tor identity can be renewed over the control port on rotation.
- All numeric config options are validated, including retry/backoff, circuit
  breaker, cooldown, navigation timeout, request count and Tor ports.
- Browser/context cleanup on scraper and exercise failures; viewport and mouse
  coordinate edge cases (negative coordinates, zero-size viewports, out-of-range
  positions) no longer raise.
- Playwright imports are guarded across every module so the package, config and
  tests work without Playwright installed; browser entry points raise an
  actionable error instead of `ImportError`.
- Console output uses a `safe_print()` helper with ASCII fallbacks, avoiding
  `UnicodeEncodeError` on legacy Windows consoles.
- Consolidated duplicate `HoneypotDetector`/`ProxyServer` definitions and
  expanded root-package exports.

### Added
- Regression tests for scraper reliability, honeypot filtering, stealth context,
  compatibility, config validation and an example smoke test.

### Changed
- Refreshed `README.md`, `architecture.txt`, `docs/structure.md`, metadata and
  dependencies to match the packaged 2.0 layout; `docs/structure.md` is now UTF-8.
- Pinned the Ruff lint rule set and target version in `pyproject.toml` and bounded
  the dev dependency to `<1`, so newer Ruff releases with expanded default rules
  no longer break CI unexpectedly.

## [2.0.0] - 2026-11-04

### Added
- Packaged the project with `pyproject.toml` and a top-level package entry point.
- Centralized version metadata (`__version__ = "2.0.0"`).
- Release notes and changelog tracking for major updates.
- Retry logic with exponential backoff and proxy failover.
- Circuit breaker and adaptive delays for reliability.
- Proxy health scoring and selection.
- Configuration validation via `__post_init__`.
- Test suite for configuration validation.

### Changed
- Updated supported-version policy in `SECURITY.md` to include the 2.0.x line.
- Refreshed project metadata and documentation for the major 2.0 release.
- Playwright import made optional for config-only/test usage.

### Notes
- This release follows a major update to the Anti-Scraping Playwright toolkit.
