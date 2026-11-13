
import time

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL
from analysis.prompts import ANALYSIS_PROMPT


client = genai.Client(api_key=GEMINI_API_KEY)

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAYS = [30, 60]

# Counts actual Gemini request attempts, including retries.
API_CALL_COUNT = 0


def get_api_call_count():
    """Return the number of Gemini API attempts."""

    return API_CALL_COUNT


def reset_api_call_count():
    """Reset the API attempt counter."""

    global API_CALL_COUNT
    API_CALL_COUNT = 0


def is_retryable_error(error):
    """
    Identify temporary errors that may succeed on retry.
    Do not retry permanent errors such as invalid API keys.
    """

    message = str(error).lower()

    retryable_indicators = [
        "429",
        "resource_exhausted",
        "rate limit",
        "500",
        "internal server error",
        "502",
        "503",
        "service unavailable",
        "504",
        "deadline exceeded",
        "timed out",
        "timeout",
        "connection error"
    ]

    return any(
        indicator in message
        for indicator in retryable_indicators
    )


def analyze_page(
    page_content,
    source_type="vendor_article_or_other"
):
    """
    Analyze webpage content using Gemini.

    Includes limited retries for temporary API failures.
    """

    global API_CALL_COUNT

    prompt = ANALYSIS_PROMPT.replace(
        "{source_type}",
        source_type
    ).replace(
        "{page_content}",
        page_content
    )

    for attempt in range(MAX_RETRIES + 1):

        try:
            API_CALL_COUNT += 1

            print(
                f"Gemini API attempt: {API_CALL_COUNT}"
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as error:

            if (
                is_retryable_error(error)
                and attempt < MAX_RETRIES
            ):

                wait_time = RETRY_DELAYS[attempt]

                print(
                    f"Temporary Gemini API error: {error}"
                )

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:
                print(
                    f"Gemini analysis failed: {error}"
                )
                raise
