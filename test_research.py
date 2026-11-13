
from services.pipeline import run_research

results = run_research(
    topic="WhatsApp automation problems for small businesses",
    keywords=[
        "customer support",
        "automation",
        "business problems"
    ],
    max_pages=35
)

print("\n========== RESEARCH SUMMARY ==========")

print("Pages discovered:", results["crawl_results"]["total_discovered"])
print("Pages scraped:", results["crawl_results"]["total_scraped"])
print("Pages analysed:", len(results["analyzed_pages"]))
print("Opportunities found:", len(results["opportunities"]))
print("AI briefs generated:", len(results["opportunity_briefs"]))

print("\n========== TOP OPPORTUNITY BRIEFS ==========")

for index, brief in enumerate(results["opportunity_briefs"], start=1):
    print(f"\nOpportunity {index}")
    print("Problem:", brief["problem"])
    print("Affected users:", brief["who_is_affected"])
    print("Product idea:", brief["possible_product_idea"])
    print("Score:", brief["opportunity_score"])
    print("Evidence:", len(brief["evidence"]))
