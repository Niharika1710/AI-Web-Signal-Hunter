from analysis.opportunity_ranker import calculate_opportunity_score

score = calculate_opportunity_score(
    frequency=80,
    relevance=90,
    urgency=70,
    confidence=95,
    recency=100
)

print("Opportunity score:", score)