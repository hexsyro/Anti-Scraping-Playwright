.PHONY: install test lint

install:
	pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m compileall anti_scraping_playwright tests examples