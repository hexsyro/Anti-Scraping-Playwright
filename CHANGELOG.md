# Changelog

All notable changes to this project are documented in this file.

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
