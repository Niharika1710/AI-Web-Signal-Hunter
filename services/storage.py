
import json
import hashlib
from pathlib import Path

CACHE_FILE = Path("data/analysis_cache.json")

# Change this version whenever the analysis prompt or logic changes.
CACHE_VERSION = "v2"

def get_page_key(page_content, source_type="vendor_article_or_other"):
    """Create a unique key for content, source type and cache version."""

    cache_input = (
        f"{CACHE_VERSION}|{source_type}|{page_content}"
    )

    return hashlib.sha256(
        cache_input.encode("utf-8")
    ).hexdigest()


def load_cache():
    """Load previously saved analyses."""

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_analysis(page_content, analysis, source_type="vendor_article_or_other"):
    """Save a successful analysis to the cache."""

    cache = load_cache()

    key = get_page_key(page_content, source_type)

    cache[key] = analysis

    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=4, ensure_ascii=False)


def get_cached_analysis(page_content, source_type="vendor_article_or_other"):
    """Retrieve a cached analysis."""

    cache = load_cache()

    key = get_page_key(page_content, source_type)

    return cache.get(key)
