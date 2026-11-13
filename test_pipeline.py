from services.pipeline import run_crawl, analyze_pages
from analysis.opportunity_ranker import rank_opportunities

results = run_crawl(
    topic="WhatsApp automation problems for small businesses",
    keywords=["customer support", "pricing"],
    max_pages=5
)

print("\n========== CRAWL SUMMARY ==========")

print("Topic:", results["topic"])
print("URLs discovered:", results["total_discovered"])
print("Pages successfully scraped:", results["total_scraped"])
print("Pages failed:", results["total_failed"])

print("\n========== SUCCESSFUL PAGES ==========")

for page in results["pages"]:
    print(page["title"])
    print(page["url"])
    print("-" * 40)

print("\n========== GEMINI ANALYSIS ==========")

analyzed_pages = analyze_pages(results["pages"])

if analyzed_pages:
    total_domains = len({
        page["source_domain"]
        for page in analyzed_pages
    })

    opportunities = rank_opportunities(
        analyzed_pages,
        total_domains
    )

    print("\n===== RANKED OPPORTUNITIES =====")

    for index, opportunity in enumerate(opportunities, start=1):
        print(f"\nOpportunity {index}")
        print("Theme:", opportunity["theme"])
        print("Category:", opportunity["category"])
        print("Signals:", opportunity["signal_count"])
        print("Score:", opportunity["opportunity_score"])

print("\n========== ANALYSIS RESULTS ==========")

for item in analyzed_pages:
    print("\nCategory:", item["category"])
    print("Summary:", item["summary"])
    print("Relevance:", item["relevance_score"])
    print("Urgency:", item["urgency_score"])
    print("Confidence:", item["confidence_score"])
    print("Source:", item["url"])
    print("-" * 50)

print("\nTotal analysed:", len(analyzed_pages))
