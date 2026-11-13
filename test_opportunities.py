from analysis.opportunity_ranker import rank_opportunities

sample_pages = [
    {
        "category": "pain_point",
        "summary": "Small businesses struggle to manage too many WhatsApp messages.",
        "relevance_score": 90,
        "urgency_score": 85,
        "confidence_score": 95,
        "source_domain": "example.com",
        "crawl_date": "2026-11-13T10:00:00+00:00"
    },
    {
        "category": "pain_point",
        "summary": "Businesses find it difficult to handle large volumes of WhatsApp messages.",
        "relevance_score": 85,
        "urgency_score": 80,
        "confidence_score": 90,
        "source_domain": "another.com",
        "crawl_date": "2026-11-13T10:00:00+00:00"
    },
    {
        "category": "feature_request",
        "summary": "Users want automated customer reply features.",
        "relevance_score": 80,
        "urgency_score": 70,
        "confidence_score": 90,
        "source_domain": "third.com",
        "crawl_date": "2026-11-13T10:00:00+00:00"
    }
]

opportunities = rank_opportunities(
    analyzed_pages=sample_pages,
    total_domains=3
)

for index, opportunity in enumerate(opportunities, start=1):
    print(f"\nOpportunity {index}")
    print("Category:", opportunity["category"])
    print("Theme:", opportunity["theme"])
    print("Signal count:", opportunity["signal_count"])
    print("Frequency:", opportunity["frequency_score"])
    print("Final score:", opportunity["opportunity_score"])