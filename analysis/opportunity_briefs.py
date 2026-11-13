
import json
import hashlib
from pathlib import Path

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL
from analysis.brief_prompts import BRIEF_PROMPT


client = genai.Client(api_key=GEMINI_API_KEY)

BRIEF_CACHE_FILE = Path("data/brief_cache.json")
BRIEF_CACHE_VERSION = "v2"


def load_brief_cache():
    """Load previously generated opportunity briefs."""

    BRIEF_CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not BRIEF_CACHE_FILE.exists():
        return {}

    try:
        with open(
            BRIEF_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_brief_cache(cache):
    """Save generated briefs."""

    BRIEF_CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        BRIEF_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            cache,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_brief_cache_key(opportunity):
    """
    Generate a unique cache key using the opportunity,
    evidence, model and prompt version.
    """

    cache_data = {
        "version": BRIEF_CACHE_VERSION,
        "model": GEMINI_MODEL,
        "category": opportunity["category"],
        "theme": opportunity["theme"],
        "evidence": [
            {
                "summary": signal.get("summary", ""),
                "excerpt": signal.get("supporting_excerpt", ""),
                "url": signal.get("url", "")
            }
            for signal in opportunity.get("evidence", [])
        ]
    }

    serialized = json.dumps(
        cache_data,
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()


def generate_opportunity_brief(opportunity):
    """
    Generate a basic structured opportunity brief.
    This function does not call Gemini.
    """

    signals = opportunity["evidence"]

    evidence = []

    for signal in signals:
        evidence.append({
            "summary": signal["summary"],
            "supporting_excerpt": signal["supporting_excerpt"],
            "source_url": signal["url"]
        })

    return {
        "opportunity": opportunity["theme"],
        "category": opportunity["category"],
        "problem": opportunity["theme"],
        "who_is_affected": "Not established by the available evidence.",
        "why_it_matters": (
            f"This opportunity has {opportunity['signal_count']} "
            f"signals across {opportunity.get('unique_domain_count', 0)} "
            "distinct domains. Further validation is needed."
        ),
        "possible_product_idea": (
            "Explore possible solutions through customer interviews "
            "and additional research."
        ),
        "opportunity_score": opportunity["opportunity_score"],
        "evidence_strength": opportunity.get(
            "evidence_strength",
            "unknown"
        ),
        "evidence": evidence,
        "next_validation_step": (
            "Interview relevant users and verify whether they "
            "experience this problem regularly."
        )
    }


def generate_ai_opportunity_brief(opportunity):
    """
    Generate an AI-powered opportunity brief using Gemini.
    Reuse cached briefs to reduce API calls.
    """

    # 1. Generate cache key
    cache_key = get_brief_cache_key(opportunity)

    # 2. Check cache
    cache = load_brief_cache()

    if cache_key in cache:
        print("Using cached opportunity brief. Gemini call skipped!")

        ai_brief = cache[cache_key].copy()

    else:
        print("Generating a new AI opportunity brief...")

        # 3. Prepare evidence
        evidence_data = [
            {
                "summary": signal.get("summary", ""),
                "supporting_excerpt": signal.get(
                    "supporting_excerpt", ""
                ),
                "source_domain": signal.get("source_domain", ""),
                "source_url": signal.get("url", ""),
                "source_type": signal.get("source_type", "")
            }
            for signal in opportunity["evidence"]
        ]

        evidence_text = json.dumps(
            evidence_data,
            indent=2,
            ensure_ascii=False
        )

        # 4. Build prompt
        prompt = (
            BRIEF_PROMPT
            .replace("{opportunity}", opportunity["theme"])
            .replace("{category}", opportunity["category"])
            .replace(
                "{evidence_strength}",
                opportunity.get("evidence_strength", "unknown")
            )
            .replace(
                "{unique_domain_count}",
                str(opportunity.get("unique_domain_count", 0))
            )
            .replace(
                "{evidence}",
                evidence_text
            )
        )

        # 5. Call Gemini
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty brief."
            )

        # 6. Parse JSON
        response_text = response.text.strip()

        if response_text.startswith("```"):
            response_text = response_text.split(
                "\n",
                1
            )[1].rsplit(
                "```",
                1
            )[0].strip()

        try:
            ai_brief = json.loads(response_text)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Gemini returned invalid JSON for the opportunity brief."
            ) from error

        # 7. Validate required fields
        required_fields = [
            "problem",
            "who_is_affected",
            "why_it_matters",
            "possible_product_idea",
            "next_validation_step"
        ]

        for field in required_fields:
            if (
                field not in ai_brief
                or not isinstance(ai_brief[field], str)
                or not ai_brief[field].strip()
            ):
                raise ValueError(
                    f"Missing or invalid brief field: {field}"
                )

        # 8. Cache successful brief
        cache[cache_key] = ai_brief

        save_brief_cache(cache)

    # 9. Attach current opportunity information
    return {
        **ai_brief,
        "opportunity": opportunity["theme"],
        "category": opportunity["category"],
        "opportunity_score": opportunity["opportunity_score"],
        "evidence_strength": opportunity.get(
            "evidence_strength",
            "unknown"
        ),
        "unique_domain_count": opportunity.get(
            "unique_domain_count",
            0
        ),
        "evidence": opportunity["evidence"]
    }
