
from datetime import datetime, timezone
from difflib import SequenceMatcher
from collections import defaultdict


def calculate_opportunity_score(
    frequency,
    relevance,
    urgency,
    confidence,
    recency
):
    """
    Calculate a transparent opportunity score.
    All input values must be between 0 and 100.
    """

    values = [
        frequency,
        relevance,
        urgency,
        confidence,
        recency
    ]

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0 <= value <= 100
        for value in values
    ):
        raise ValueError("All scores must be between 0 and 100.")

    score = (
        0.30 * frequency +
        0.25 * relevance +
        0.20 * urgency +
        0.15 * confidence +
        0.10 * recency
    )

    return round(score, 2)


def normalize_text(text):
    """Normalize text before comparing signal summaries."""

    return " ".join(
        str(text).lower().strip().split()
    )


def group_signals(analyzed_pages, similarity_threshold=0.65):
    """
    Group similar signals only when they share a category.
    """

    groups = []

    for page in analyzed_pages:

        summary = normalize_text(page.get("summary", ""))
        category = page.get("category")

        if not summary or not category:
            continue

        matched_group = None

        for group in groups:

            if group["category"] != category:
                continue

            similarity = SequenceMatcher(
                None,
                summary,
                group["reference_summary"]
            ).ratio()

            if similarity >= similarity_threshold:
                matched_group = group
                break

        if matched_group:
            matched_group["signals"].append(page)

        else:
            groups.append({
                "category": category,
                "reference_summary": summary,
                "signals": [page]
            })

    return groups


def calculate_frequency_score(group, total_domains=None):
    """
    Calculate frequency using unique domains supporting
    the same opportunity.

    Frequency is the percentage of analyzed signal-bearing
    domains that support this opportunity.
    """

    relevant_domains = {
        signal.get("source_domain")
        for signal in group["signals"]
        if signal.get("source_domain")
    }

    if total_domains is None:
        denominator = len({
            signal.get("source_domain")
            for group_item in group.get("signals", [])
            if (signal := group_item).get("source_domain")
        })
    else:
        denominator = total_domains

    if denominator <= 0:
        return 0

    frequency = (
        len(relevant_domains) / denominator
    ) * 100

    return round(min(frequency, 100), 2)


def calculate_recency_score(crawl_date):
    """
    Calculate crawl recency.

    This measures when the page was collected,
    not when the original content was published.
    """

    try:
        crawled_at = datetime.fromisoformat(
            crawl_date.replace("Z", "+00:00")
        )

        if crawled_at.tzinfo is None:
            crawled_at = crawled_at.replace(
                tzinfo=timezone.utc
            )

        current_time = datetime.now(timezone.utc)

        age_days = (
            current_time - crawled_at
        ).total_seconds() / 86400

        score = max(0, 100 - (age_days * 10))

        return round(score, 2)

    except (ValueError, TypeError, AttributeError):
        return 0


def rank_opportunities(analyzed_pages, total_domains=None):
    """
    Group signals, calculate transparent scores,
    and rank opportunities.
    """

    relevant_pages = [
        page for page in analyzed_pages
        if page.get("category") != "irrelevant"
    ]

    # Only count domains that produced a relevant signal.
    signal_domains = {
        page.get("source_domain")
        for page in relevant_pages
        if page.get("source_domain")
    }

    effective_total_domains = len(signal_domains)

    groups = group_signals(relevant_pages)

    opportunities = []

    for group in groups:

        signals = group["signals"]

        unique_domains = {
            signal.get("source_domain")
            for signal in signals
            if signal.get("source_domain")
        }

        frequency = calculate_frequency_score(
            group,
            effective_total_domains
        )

        relevance = sum(
            signal["relevance_score"]
            for signal in signals
        ) / len(signals)

        urgency = sum(
            signal["urgency_score"]
            for signal in signals
        ) / len(signals)

        confidence = sum(
            signal["confidence_score"]
            for signal in signals
        ) / len(signals)

        recency_scores = [
            calculate_recency_score(signal["crawl_date"])
            for signal in signals
            if signal.get("crawl_date")
        ]

        recency = (
            sum(recency_scores) / len(recency_scores)
            if recency_scores else 0
        )

        final_score = calculate_opportunity_score(
            frequency,
            relevance,
            urgency,
            confidence,
            recency
        )

        evidence_count = len(signals)
        domain_count = len(unique_domains)

        if domain_count == 1:
            evidence_strength = "single_source"
        elif domain_count < 3:
            evidence_strength = "limited_evidence"
        else:
            evidence_strength = "multi_source"

        opportunities.append({
            "category": group["category"],
            "theme": group["reference_summary"],
            "signal_count": evidence_count,
            "unique_domain_count": domain_count,
            "evidence_strength": evidence_strength,
            "frequency_score": frequency,
            "relevance_score": round(relevance, 2),
            "urgency_score": round(urgency, 2),
            "confidence_score": round(confidence, 2),
            "recency_score": round(recency, 2),
            "opportunity_score": final_score,
            "evidence": signals
        })

    opportunities.sort(
        key=lambda item: item["opportunity_score"],
        reverse=True
    )

    return opportunities
