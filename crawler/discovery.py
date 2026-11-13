
from tavily import TavilyClient
from config import TAVILY_API_KEY

from urllib.parse import (
    urlparse,
    urlunparse,
    parse_qsl,
    urlencode
)
import math


client = TavilyClient(api_key=TAVILY_API_KEY)


# Sources that may contain independent customer evidence.
REVIEW_DOMAINS = {
    "g2.com",
    "capterra.com",
    "trustpilot.com",
    "getapp.com",
    "softwareadvice.com",
    "producthunt.com",
    "trustradius.com"
}

# Public discussion and technical community platforms.
DISCUSSION_DOMAINS = {
    "stackoverflow.com",
    "github.com",
    "news.ycombinator.com",
    "community.n8n.io",
    "community.make.com",
    "community.zapier.com",
    "discuss.python.org"
}

# Some platforms frequently restrict automated page access.
# They are not excluded, but are given lower discovery priority.
RESTRICTED_LIKELY_DOMAINS = {
    "reddit.com",
    "g2.com",
    "capterra.com",
    "trustradius.com"
}

EXCLUDED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "play.google.com"
}

CUSTOMER_TERMS = [
    "customer complaint",
    "user complaint",
    "frustrated",
    "struggling",
    "problem",
    "issue",
    "real experience",
    "my experience",
    "we use",
    "i use",
    "does anyone",
    "looking for",
    "recommendation",
    "wish it had",
    "missing feature",
    "feature request",
    "too expensive",
    "pricing problem",
    "alternative"
]

PROMOTIONAL_TERMS = [
    "start free trial",
    "book a demo",
    "sign up now",
    "get started",
    "buy now",
    "limited time offer",
    "contact sales"
]

PROMOTIONAL_TITLE_TERMS = [
    "complete guide",
    "ultimate guide",
    "step by step",
    "top 10",
    "best tools",
    "best platforms",
    "how to use",
    "everything you need to know"
]


def normalize_domain(url):
    """Return a normalized hostname."""

    domain = (urlparse(url).hostname or "").lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def domain_matches(domain, known_domain):
    """Match a domain or one of its subdomains."""

    return (
        domain == known_domain
        or domain.endswith("." + known_domain)
    )


def normalize_url(url):
    """
    Remove fragments and common tracking parameters
    to improve duplicate detection.
    """

    parsed = urlparse(url)

    tracking_parameters = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "ref",
        "referrer"
    }

    clean_query = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True
        )
        if key.lower() not in tracking_parameters
    ]

    return urlunparse(
        parsed._replace(
            fragment="",
            query=urlencode(clean_query),
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower()
        )
    ).rstrip("/")


def is_discussion_domain(domain):
    """Identify known or recognizable community domains."""

    if any(
        domain_matches(domain, item)
        for item in DISCUSSION_DOMAINS
    ):
        return True

    labels = domain.split(".")

    return any(
        label in {"community", "forum", "forums", "discuss"}
        for label in labels
    )


def is_review_domain(domain):
    return any(
        domain_matches(domain, item)
        for item in REVIEW_DOMAINS
    )


def get_result_score(result, query_priority):
    """
    Rank candidate URLs by likely evidence usefulness
    and source accessibility.

    This is only a discovery heuristic. Gemini and the
    evidence validator make the final signal decision.
    """

    url = result.get("url", "")
    domain = normalize_domain(url)

    title = result.get("title", "").lower()
    content = result.get("content", "").lower()
    path = urlparse(url).path.lower()

    combined_text = f"{title} {content}"

    score = query_priority

    # Public community and technical discussions.
    if is_discussion_domain(domain):
        score += 25

    # Independent review platforms.
    if is_review_domain(domain):
        score += 12

    # Issue trackers can contain direct reports of problems.
    if domain_matches(domain, "github.com") and "/issues" in path:
        score += 15

    # Customer-language indicators.
    matched_terms = sum(
        1
        for term in CUSTOMER_TERMS
        if term in combined_text
    )

    score += min(matched_terms * 4, 24)

    # Deprioritize sources that frequently restrict crawling.
    if any(
        domain_matches(domain, item)
        for item in RESTRICTED_LIKELY_DOMAINS
    ):
        score -= 18

    # Deprioritize promotional and vendor-oriented material.
    if any(
        term in combined_text
        for term in PROMOTIONAL_TERMS
    ):
        score -= 8

    if any(
        term in title
        for term in PROMOTIONAL_TITLE_TERMS
    ):
        score -= 8

    if any(
        section in path
        for section in (
            "/blog/",
            "/resources/",
            "/guides/",
            "/webinars/"
        )
    ):
        score -= 5

    # Avoid G2 tracking redirect links.
    if "event_tracking" in path or "external_clicks" in path:
        score -= 100

    return score


def build_search_queries(topic, keyword_text):
    """Build diverse searches around real customer language."""

    return [
        (
            f'"{topic}" customer complaints problems frustrations '
            f'{keyword_text}',
            45
        ),
        (
            f'"{topic}" "I have a problem" OR "I struggle" '
            f'OR "my experience" {keyword_text}',
            44
        ),
        (
            f'"{topic}" "does anyone use" OR "has anyone tried" '
            f'OR "what do you recommend" {keyword_text}',
            44
        ),
        (
            f'"{topic}" small business owner discussion '
            f'customer experience {keyword_text}',
            42
        ),
        (
            f'"{topic}" missing features feature requests '
            f'user feedback {keyword_text}',
            40
        ),
        (
            f'"{topic}" expensive pricing concerns hidden costs '
            f'customer complaints {keyword_text}',
            39
        ),
        (
            f'"{topic}" alternative recommendation real users '
            f'community discussion {keyword_text}',
            40
        ),
        (
            f'"{topic}" reviews pros cons actual user experience '
            f'{keyword_text}',
            38
        ),
        (
            f'site:stackoverflow.com "{topic}" problems API issues '
            f'{keyword_text}',
            36
        ),
        (
            f'site:github.com "{topic}" issues feature request '
            f'bug problem {keyword_text}',
            36
        ),
        (
            f'site:community.n8n.io OR site:community.make.com '
            f'"{topic}" {keyword_text}',
            35
        ),
        (
            f'site:reddit.com "{topic}" complaint experience '
            f'problems recommendation {keyword_text}',
            30
        )
    ]


def discover_urls(topic, keywords=None, max_pages=25):
    """
    Discover customer-oriented webpages across multiple
    domains. Returns URLs for the existing scraper.
    """

    if not topic or not topic.strip():
        raise ValueError("Please provide a research topic.")

    if max_pages <= 0:
        raise ValueError("max_pages must be greater than zero.")

    if isinstance(keywords, str):
        keyword_text = keywords.strip()
    else:
        keyword_text = " ".join(keywords) if keywords else ""

    search_queries = build_search_queries(
        topic.strip(),
        keyword_text
    )

    candidates = {}
    search_failures = []

    # Search all query patterns before selecting URLs.
    for query, priority in search_queries:

        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=10,
                topic="general"
            )

            results = response.get("results", [])

            print(f"\nQuery: {query}")
            print(f"Tavily returned: {len(results)} results")

        except Exception as error:

            print(f"Search failed: {error}")

            search_failures.append({
                "query": query,
                "error": str(error)
            })

            continue

        for result in results:

            url = result.get("url", "")

            if not url:
                continue

            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                continue

            domain = normalize_domain(url)

            if not domain:
                continue

            if any(
                domain_matches(domain, excluded)
                for excluded in EXCLUDED_DOMAINS
            ):
                continue

            # Reject known tracking redirect endpoints.
            if (
                "event_tracking" in parsed.path.lower()
                or "external_clicks" in parsed.path.lower()
            ):
                continue

            normalized_url = normalize_url(url)

            score = get_result_score(
                result,
                priority
            )

            candidate = {
                "url": url,
                "domain": domain,
                "score": score,
                "title": result.get("title", ""),
                "snippet": result.get("content", "")
            }

            if (
                normalized_url not in candidates
                or score > candidates[normalized_url]["score"]
            ):
                candidates[normalized_url] = candidate

    # Sort highest scoring sources first.
    ranked_candidates = sorted(
        candidates.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    discovered_urls = []
    domain_counts = {}

    # Limit repeated pages from one domain.
    max_per_domain = max(
        2,
        min(4, math.ceil(max_pages / 10))
    )

    for candidate in ranked_candidates:

        if len(discovered_urls) >= max_pages:
            break

        domain = candidate["domain"]

        if domain_counts.get(domain, 0) >= max_per_domain:
            continue

        discovered_urls.append(candidate["url"])

        domain_counts[domain] = (
            domain_counts.get(domain, 0) + 1
        )

    print("\n========== URL DISCOVERY SUMMARY ==========")
    print("Unique candidates:", len(candidates))
    print("Selected URLs:", len(discovered_urls))
    print("Unique domains:", len(domain_counts))
    print("Search failures:", len(search_failures))

    print("\nSelected sources:")

    selected = set(discovered_urls)

    for candidate in ranked_candidates:

        if candidate["url"] in selected:

            print(
                f"{candidate['domain']} | "
                f"Score: {candidate['score']} | "
                f"{candidate['title']}"
            )

    return discovered_urls
