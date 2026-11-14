.PHONY: install test lint workflow

install:
	pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m compileall anti_scraping_playwright tests examples

workflow: lint
	python -m ruff check .
	python -m pytest -q