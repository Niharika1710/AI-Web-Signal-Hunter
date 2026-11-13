
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse


USER_AGENT = "AIWebSignalHunter/1.0 (research prototype)"
robots_cache = {}

REQUEST_TIMEOUT = 10


def can_scrape(url):
    """
    Check whether scraping a URL is permitted by robots.txt.

    Fail closed when permission cannot be verified.
    """

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    robots_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        "/robots.txt",
        "",
        "",
        ""
    ))

    # Reuse previously checked robots rules.
    if robots_url in robots_cache:
        return robots_cache[robots_url].can_fetch(
            USER_AGENT,
            url
        )

    try:
        response = requests.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )

        # Explicitly deny access for restricted or rate-limited requests.
        if response.status_code in (401, 403, 429):
            return False

        # Server errors: permission cannot be verified.
        if response.status_code >= 500:
            return False

        # Other client errors are not treated as permission.
        if 400 <= response.status_code < 500:
            return False

        # Successful robots.txt response.
        if response.status_code == 200:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())

            robots_cache[robots_url] = parser

            return parser.can_fetch(USER_AGENT, url)

        # Redirect or unexpected response: fail closed.
        return False

    except requests.RequestException as error:
        print(f"Could not check robots.txt: {error}")
        return False
