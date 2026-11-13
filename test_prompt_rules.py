
from analysis.llm_analyzer import analyze_page
from analysis.validator import validate_analysis

samples = [
    """
    Sign Up Now! Start your free trial of our WhatsApp
    automation platform today.
    """,

    """
    We are a small business and WhatsApp automation keeps
    failing when we send messages to customers. We need
    a more reliable solution.
    """,

    """
    Is there any affordable WhatsApp automation tool?
    Our current provider charges too much for message delivery.
    """
]

for index, sample in enumerate(samples, start=1):

    print(f"\nTEST CASE {index}")

    raw_response = analyze_page(sample)
    result = validate_analysis(raw_response)

    print("Category:", result["category"])
    print("Excerpt:", result["supporting_excerpt"])
    print("Reason:", result["reason"])
