from analysis.opportunity_briefs import get_brief_cache_key

opportunity = {
    "category": "pain_point",
    "theme": "Small businesses struggle with WhatsApp messages",
    "evidence": [
        {
            "summary": "Businesses struggle to manage messages",
            "supporting_excerpt": "Managing customer messages is difficult",
            "url": "https://example.com/review"
        }
    ]
}

key1 = get_brief_cache_key(opportunity)
key2 = get_brief_cache_key(opportunity)

print("Cache key:", key1)
print("Same input produces same key:", key1 == key2)