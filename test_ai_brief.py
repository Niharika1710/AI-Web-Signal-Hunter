from analysis.opportunity_briefs import generate_ai_opportunity_brief

sample_opportunity = {
    "theme": "Small businesses struggle to manage large volumes of WhatsApp messages.",
    "category": "pain_point",
    "signal_count": 2,
    "opportunity_score": 82.07,
    "evidence": [
        {
            "summary": "Small businesses struggle with customer messages.",
            "supporting_excerpt": "Managing hundreds of customer messages is difficult.",
            "url": "https://example.com/article1"
        },
        {
            "summary": "Businesses need better WhatsApp support.",
            "supporting_excerpt": "Our team cannot handle all incoming enquiries.",
            "url": "https://another.com/article2"
        }
    ]
}

brief = generate_ai_opportunity_brief(sample_opportunity)

print("\n===== GEMINI GENERATED OPPORTUNITY BRIEF =====")

for key, value in brief.items():
    print(f"\n{key}: {value}")