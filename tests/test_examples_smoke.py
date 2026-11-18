"""The documented exercise must only call APIs that actually exist."""

from pathlib import Path

from anti_scraping_playwright import AntiBlockingScraper

EXERCISE = Path(__file__).resolve().parents[1] / "examples" / "exercise.py"


def test_exercise_uses_existing_scraper_api():
    source = EXERCISE.read_text(encoding="utf-8")

    assert "scrape_single" not in source
    assert "scrape_with_rotation" in source
    assert hasattr(AntiBlockingScraper, "scrape_with_rotation")


def test_exercise_uses_valid_selector_for_numeric_ids():
    source = EXERCISE.read_text(encoding="utf-8")

    assert '[id="{article_id}"]' in source
