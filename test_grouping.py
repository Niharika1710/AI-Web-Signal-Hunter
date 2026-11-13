from analysis.opportunity_ranker import group_signals

sample_signals = [
    {
        "category": "pain_point",
        "summary": "Small businesses struggle to manage too many WhatsApp messages."
    },
    {
        "category": "pain_point",
        "summary": "Businesses find it difficult to handle large volumes of WhatsApp messages."
    },
    {
        "category": "feature_request",
        "summary": "Users want automated customer reply features."
    }
]

groups = group_signals(sample_signals)

for index, group in enumerate(groups, start=1):
    print(f"\nGroup {index}")
    print("Category:", group["category"])
    print("Number of signals:", len(group["signals"]))
    print("Reference:", group["reference_summary"])