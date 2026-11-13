from analysis.opportunity_ranker import calculate_frequency_score

sample_group = {
    "signals": [
        {"source_domain": "example.com"},
        {"source_domain": "another.com"},
        {"source_domain": "third.com"},
        {"source_domain": "example.com"}
    ]
}

score = calculate_frequency_score(
    sample_group,
    total_domains=5
)

print("Frequency score:", score)