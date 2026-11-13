
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

# Create Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Send a simple test prompt
response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents="Explain what web scraping is in two simple sentences."
)

# Display Gemini response
print("\nGemini API connection successful!")
print("Response:")
print(response.text)
