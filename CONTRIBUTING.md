# Contributing to Anti-Scraping

Thank you for your interest in contributing!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes

## Testing

Run the full workflow test suite (the same checks that run in GitHub Actions) before
opening a pull request so bugs are caught locally first:

```bash
make workflow
```

This runs lint (compileall + ruff) and the test suite. At minimum, run:

```bash
python -m pytest -q
python -m ruff check .
python -m compileall anti_scraping_playwright tests examples
```

Run tests with:

```bash
pytest
```

Pull requests are gated by the `CI` workflow (`.github/workflows/ci.yml`), which
runs the same checks across Python 3.10–3.13. A pull request that fails these
checks cannot be merged, so please run them locally first to identify bugs early.

## Questions?

Open an issue for questions about contributing.
