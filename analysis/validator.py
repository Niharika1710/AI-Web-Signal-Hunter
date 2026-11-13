
import json


def validate_analysis(raw_response):
    """
    Convert Gemini's response into JSON
    and validate the required fields.
    """

    try:
        result = json.loads(raw_response)

        required_fields = [
            "category",
            "summary",
            "supporting_excerpt",
            "relevance_score",
            "urgency_score",
            "confidence_score",
            "reason"
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing field: {field}")

        valid_categories = [
            "pain_point",
            "buying_signal",
            "feature_request",
            "pricing_concern",
            "competitor_activity",
            "irrelevant"
        ]

        if result["category"] not in valid_categories:
            raise ValueError("Invalid category")

        for field in [
            "relevance_score",
            "urgency_score",
            "confidence_score"
        ]:
            score = result[field]

            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise ValueError(f"{field} must be a number")

            if not 0 <= score <= 100:
                raise ValueError(f"{field} must be between 0 and 100")

        if len(result["supporting_excerpt"].split()) > 30:
            raise ValueError("Supporting excerpt exceeds 30 words")

        return result

    except json.JSONDecodeError as error:
        raise ValueError("Gemini returned invalid JSON") from error

import re


def validate_supporting_excerpt(excerpt, page_content):
    """
    Verify that the AI-generated excerpt exists
    in the original webpage content.
    """

    if not excerpt or not excerpt.strip():
        return False

    def normalize(text):
        text = text.casefold()
        text = re.sub(r"[^\w\s]", "", text)
        text = " ".join(text.split())
        return text

    normalized_excerpt = normalize(excerpt)
    normalized_content = normalize(page_content)

    if not normalized_excerpt:
        return False

    return normalized_excerpt in normalized_content
