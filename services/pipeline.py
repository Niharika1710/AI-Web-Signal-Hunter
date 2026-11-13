
import json
import time
import traceback

from analysis.opportunity_ranker import rank_opportunities
from analysis.opportunity_briefs import generate_ai_opportunity_brief

from crawler.discovery import discover_urls
from crawler.scraper import scrape_page

from analysis.llm_analyzer import (
    analyze_page,
    get_api_call_count
)

from analysis.validator import (
    validate_analysis,
    validate_supporting_excerpt
)

from services.storage import (
    get_cached_analysis,
    save_analysis
)


def run_crawl(topic, keywords=None, max_pages=25):
    """
    Discover additional URLs and scrape until the requested
    number of unique, successfully scraped pages is reached.
    """

    if max_pages <= 0:
        raise ValueError("max_pages must be greater than zero.")

    # Discover extra URLs to compensate for failed pages.
    discovery_limit = max_pages * 2

    urls = discover_urls(
        topic=topic,
        keywords=keywords,
        max_pages=discovery_limit
    )

    successful_pages = []
    failed_pages = []
    seen_content = set()

    print(f"\nDiscovered {len(urls)} candidate URLs.")
    print(f"Target successful pages: {max_pages}")

    for index, url in enumerate(urls, start=1):

        if len(successful_pages) >= max_pages:
            break

        print(f"\nScraping candidate {index}/{len(urls)}:")
        print(url)

        try:
            page = scrape_page(url)

            # Avoid duplicate webpage content.
            content_key = hash(page["content"])

            if content_key in seen_content:
                print("Skipped duplicate webpage content.")
                continue

            seen_content.add(content_key)
            successful_pages.append(page)

            print("Successfully scraped:", page["title"])
            print("Source type:", page.get("source_type", "unknown"))
            print(
                "Successful pages:",
                len(successful_pages),
                "/",
                max_pages
            )

        except Exception as error:

            print("Could not scrape:", error)

            failed_pages.append({
                "url": url,
                "error": str(error)
            })

    unique_domains = {
        page["source_domain"].lower().removeprefix("www.")
        for page in successful_pages
    }

    return {
        "topic": topic,
        "target_pages": max_pages,
        "total_discovered": len(urls),
        "total_scraped": len(successful_pages),
        "total_failed": len(failed_pages),
        "unique_domains": len(unique_domains),
        "target_reached": len(successful_pages) >= max_pages,
        "pages": successful_pages,
        "failures": failed_pages
    }


def analyze_pages(pages):
    """
    Analyze webpages using Gemini and reuse cached results.
    Validate both cached and newly generated analyses.
    """

    analyzed_pages = []

    for index, page in enumerate(pages, start=1):

        print(
            f"\nAnalysing page {index}/{len(pages)}: "
            f"{page['title']}"
        )

        try:
            source_type = page.get(
                "source_type",
                "vendor_article_or_other"
            )

            # 1. Look for cached analysis.
            cached = get_cached_analysis(
                page["content"],
                source_type
            )

            if cached:

                print("Cached analysis found. Gemini call skipped!")

                # Validate cached data using the same validator.
                analysis = validate_analysis(
                    json.dumps(cached)
                )

            else:

                # 2. Analyze new content.
                time.sleep(5)

                raw_response = analyze_page(
                    page["content"],
                    source_type
                )

                # 3. Validate Gemini response.
                analysis = validate_analysis(raw_response)

            # 4. Validate supporting evidence.
            if analysis["category"] != "irrelevant":

                if not validate_supporting_excerpt(
                    analysis["supporting_excerpt"],
                    page["content"]
                ):
                    raise ValueError(
                        "Supporting excerpt could not be verified "
                        "in the original webpage."
                    )

            # 5. Save only newly generated, validated analyses.
            if not cached:

                save_analysis(
                    page["content"],
                    analysis,
                    source_type
                )

            # 6. Attach original webpage metadata.
            analysis["title"] = page["title"]
            analysis["url"] = page["url"]
            analysis["source_domain"] = page["source_domain"]
            analysis["source_type"] = source_type
            analysis["crawl_date"] = page["crawl_date"]
            analysis["published_date"] = page.get("published_date")

            analyzed_pages.append(analysis)

            print("Analysis successful!")
            print("Category:", analysis["category"])

        except Exception as error:

            print("Analysis failed:", error)

    return analyzed_pages


def run_research(topic, keywords=None, max_pages=25):
    """
    Execute the complete web intelligence workflow.
    """

    print("\n========== AI WEB SIGNAL HUNTER ==========")

    # 1. Crawl webpages.
    crawl_results = run_crawl(
        topic=topic,
        keywords=keywords,
        max_pages=max_pages
    )

    pages = crawl_results["pages"]

    if not pages:
        raise RuntimeError(
            "No webpages could be scraped. "
            "Check the discovery results and robots permissions."
        )

    # 2. Analyze webpages.
    api_calls_before = get_api_call_count()

    analyzed_pages = analyze_pages(pages)

    api_calls_after = get_api_call_count()

    analysis_api_attempts = (
        api_calls_after - api_calls_before
    )

    # 3. Calculate unique crawled domains.
    total_domains = len({
        page["source_domain"].lower().removeprefix("www.")
        for page in pages
    })

    # 4. Rank opportunities.
    opportunities = rank_opportunities(
        analyzed_pages,
        total_domains
    )

    # 5. Generate briefs for only the top 3 opportunities.
    opportunity_briefs = []

    for opportunity in opportunities[:5]:

        try:
            brief = generate_ai_opportunity_brief(
                opportunity
            )

            opportunity_briefs.append(brief)

        except Exception as error:
            print("Brief generation failed:", error)

    # 6. Display final summary.
    print("\n========== RESEARCH SUMMARY ==========")

    print("Pages discovered:", crawl_results["total_discovered"])
    print("Pages successfully scraped:", crawl_results["total_scraped"])
    print("Pages failed:", crawl_results["total_failed"])
    print("Unique domains:", crawl_results["unique_domains"])
    print("Target reached:", crawl_results["target_reached"])

    print("Pages analyzed:", len(analyzed_pages))
    print("Opportunities identified:", len(opportunities))
    print("AI briefs generated:", len(opportunity_briefs))

    print(
        "Gemini analysis API attempts:",
        analysis_api_attempts
    )

    print("\nResearch completed.")

    # 7. Return complete results.
    return {
        "topic": topic,
        "crawl_results": crawl_results,
        "analyzed_pages": analyzed_pages,
        "opportunities": opportunities,
        "opportunity_briefs": opportunity_briefs,
        "gemini_analysis_api_attempts": analysis_api_attempts
    }
