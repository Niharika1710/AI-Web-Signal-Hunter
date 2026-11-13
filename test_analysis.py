
from analysis.llm_analyzer import analyze_page
from analysis.validator import validate_analysis


sample_content = """
I run a small business and currently use WhatsApp for customer support.
Managing hundreds of customer messages manually is difficult.
I wish there was an affordable tool to automatically respond to
common questions and organise customer enquiries.
"""


print("Sending webpage content to Gemini...")

raw_response = analyze_page(sample_content)

print("\nGemini Raw Response:")
print(raw_response)

print("\nValidating JSON response...")

validated_result = validate_analysis(raw_response)

print("\nValidation Successful!")
print(validated_result)
