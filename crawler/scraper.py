
import requests
import time

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urlparse

from crawler.robots_checker import can_scrape
from crawler.cleaner import clean_text


USER_AGENT = "AIWebSignalHunter/1.0 (research prototype)"

last_request_time = {}
REQUEST_DELAY = 2
MIN_CONTENT_LENGTH = 500


def classify_source(title, url, content):
    """
    Heuristically classify the webpage source.
    This is not a verified source-quality assessment.
    """

    text = f"{title} {url} {content[:1500]}".lower()

    if any(word in text for word in [
        "customer review", "user review", "verified review",
        "customer feedback", "pros and cons"
    ]):
        return "customer_review"

    if any(word in text for word in [
        "forum", "community discussion", "reddit",
        "user discussion", "question"
    ]):
        return "customer_discussion"

    if any(word in text for word in [
        "pricing", "plans", "subscription", "free trial"
    ]) and any(word in text for word in [
        "buy now", "book a demo", "get started",
        "start free trial", "our product"
    ]):
        return "product_or_pricing_page"

    if any(word in text for word in [
        "launches", "announces", "new feature",
        "product update", "release notes"
    ]):
        return "competitor_announcement"

    return "vendor_article_or_other"


def extract_published_date(soup):
    """
    Extract publication date from common webpage metadata.
    Returns None when no reliable date is available.
    """

    selectors = [
        ("meta", {"property": "article:published_time"}),
        ("meta", {"name": "datePublished"}),
        ("meta", {"name": "pubdate"}),
        ("meta", {"property": "og:published_time"}),
        ("time", {"itemprop": "datePublished"})
    ]

    for tag_name, attributes in selectors:
        element = soup.find(tag_name, attrs=attributes)

        if element:
            date_value = (
                element.get("content")
                or element.get("datetime")
            )

            if date_value:
                return date_value.strip()

    return None


def scrape_page(url):
    """
    Download a permitted webpage and extract its main content.
    """

    if not can_scrape(url):
        raise PermissionError(
            f"Crawling is not allowed or permission "
            f"could not be verified: {url}"
        )

    domain = urlparse(url).netloc.lower()

    # Respect the delay between requests to the same domain.
    current_time = time.time()
    previous_time = last_request_time.get(domain, 0)

    wait_time = REQUEST_DELAY - (
        current_time - previous_time
    )

    if wait_time > 0:
        time.sleep(wait_time)

    last_request_time[domain] = time.time()

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        if response.status_code == 429:
            raise requests.HTTPError(
                f"Rate limited by website (HTTP 429): {url}"
            )

        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not download webpage {url}: {error}"
        ) from error

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Extract publication date before removing elements.
    published_date = extract_published_date(soup)

    # Remove unnecessary webpage elements.
    for element in soup([
        "script", "style", "nav", "header",
        "footer", "aside", "form", "noscript"
    ]):
        element.decompose()

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else "Untitled"
    )

    # Prefer the main content area.
    main_content = (
        soup.find("main")
        or soup.body
        or soup
    )

    page_text = main_content.get_text(
        separator=" ",
        strip=True
    )

    page_text = clean_text(page_text)

    if not page_text or len(page_text) < MIN_CONTENT_LENGTH:
        raise ValueError(
            f"Insufficient webpage content "
            f"({len(page_text)} characters): {url}"
        )

    source_type = classify_source(
        title,
        url,
        page_text
    )

    return {
        "title": title,
        "url": url,
        "source_domain": urlparse(url).netloc,
        "source_type": source_type,
        "published_date": published_date,
        "crawl_date": datetime.now(timezone.utc).isoformat(),
        "content": page_text
    }
