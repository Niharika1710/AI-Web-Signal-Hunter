import json
import csv
import io
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from services.pipeline import run_research


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Web Signal Hunter",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def as_list(value: Any) -> list:
    """Return a list safely, including when a value is missing."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def get_value(data: Any, *keys: str, default=None):
    """Read the first available key from a dictionary."""
    if not isinstance(data, dict):
        return default
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_result(raw_result):
    """
    Normalize the pipeline response without changing the backend.
    The pipeline is expected to return a dictionary.
    """
    if isinstance(raw_result, dict):
        return raw_result

    if isinstance(raw_result, tuple):
        # Support a tuple response if the pipeline uses one.
        for item in raw_result:
            if isinstance(item, dict):
                return item

    raise ValueError(
        "The research pipeline did not return a dictionary. "
        "Please check the return value of run_research() in services/pipeline.py."
    )


def get_crawl_data(result):
    crawl = get_value(result, "crawl_results", "crawl_result", "crawl", default={})
    return crawl if isinstance(crawl, dict) else {}


def get_pages(result):
    return as_list(get_value(result, "analyzed_pages", "analyses", "results", default=[]))


def get_opportunities(result):
    return as_list(get_value(result, "opportunities", "ranked_opportunities", default=[]))


def get_briefs(result):
    return as_list(get_value(result, "opportunity_briefs", "briefs", "ai_briefs", default=[]))


def get_page_category(page):
    return str(get_value(page, "category", default="unknown")).strip().lower()


def get_page_title(page):
    return get_value(page, "title", "page_title", default="Untitled page")


def get_page_url(page):
    return get_value(page, "url", "source_url", default="")


def get_evidence_items(item):
    evidence = get_value(item, "evidence", "supporting_evidence", default=[])
    if isinstance(evidence, list):
        return evidence
    if isinstance(evidence, dict):
        return [evidence]
    return []


def evidence_count(item):
    count = get_value(item, "evidence_count", "signal_count", default=None)
    if count is not None:
        return safe_int(count, 0)
    return len(get_evidence_items(item))


def evidence_strength(item):
    explicit = get_value(item, "evidence_strength", default=None)
    if explicit:
        return str(explicit).replace("_", " ").title()

    count = evidence_count(item)
    if count <= 1:
        return "Single source"
    if count < 3:
        return "Limited evidence"
    return "Multiple sources"


def make_pages_dataframe(pages):
    rows = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        rows.append({
            "Category": get_value(page, "category", default="unknown"),
            "Title": get_page_title(page),
            "Source domain": get_value(page, "source_domain", default=""),
            "Source type": get_value(page, "source_type", default=""),
            "Relevance": safe_float(get_value(page, "relevance_score", default=0)),
            "Urgency": safe_float(get_value(page, "urgency_score", default=0)),
            "Confidence": safe_float(get_value(page, "confidence_score", default=0)),
            "Crawl date": get_value(page, "crawl_date", default=""),
            "URL": get_page_url(page),
            "Summary": get_value(page, "summary", default=""),
            "Supporting excerpt": get_value(page, "supporting_excerpt", "excerpt", default=""),
            "Reason": get_value(page, "reason", default=""),
        })
    return pd.DataFrame(rows)


def make_opportunities_dataframe(opportunities):
    rows = []
    for opportunity in opportunities:
        if not isinstance(opportunity, dict):
            continue
        rows.append({
            "Rank": len(rows) + 1,
            "Category": get_value(opportunity, "category", default=""),
            "Theme": get_value(opportunity, "theme", "opportunity", default=""),
            "Opportunity score": safe_float(get_value(opportunity, "opportunity_score", "score", default=0)),
            "Signal count": evidence_count(opportunity),
            "Unique domains": safe_int(get_value(opportunity, "unique_domain_count", default=0)),
            "Evidence strength": evidence_strength(opportunity),
        })
    return pd.DataFrame(rows)


def render_source_link(url, label="Open source"):
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        st.markdown(f"[{label}]({url})")
    elif url:
        st.caption(str(url))


def render_evidence(evidence):
    if not evidence:
        st.caption("No evidence links were included in the pipeline response.")
        return

    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, dict):
            st.write(item)
            continue

        title = get_value(item, "title", "page_title", default=f"Evidence source {index}")
        url = get_value(item, "url", "source_url", default="")
        domain = get_value(item, "source_domain", "domain", default="")
        excerpt = get_value(item, "supporting_excerpt", "excerpt", "quote", default="")
        summary = get_value(item, "summary", default="")

        with st.container(border=True):
            st.markdown(f"**{index}. {title}**")
            if domain:
                st.caption(domain)
            if excerpt:
                st.markdown(f"> {excerpt}")
            elif summary:
                st.write(summary)
            render_source_link(url)


def render_opportunity_card(opportunity, index):
    theme = get_value(opportunity, "theme", "opportunity", default=f"Opportunity {index}")
    category = get_value(opportunity, "category", default="Uncategorized")
    score = safe_float(get_value(opportunity, "opportunity_score", "score", default=0))
    count = evidence_count(opportunity)
    strength = evidence_strength(opportunity)
    evidence = get_evidence_items(opportunity)

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])
        with top_left:
            st.subheader(f"{index}. {theme}")
            st.caption(str(category).replace("_", " ").title())
        with top_right:
            st.metric("Score", f"{score:.1f}")

        metric_cols = st.columns(3)
        metric_cols[0].metric("Evidence items", count)
        metric_cols[1].metric(
            "Unique domains",
            safe_int(get_value(opportunity, "unique_domain_count", default=0))
        )
        metric_cols[2].metric("Evidence strength", strength)

        if count <= 1 or "single" in strength.lower():
            st.warning(
                "Preliminary — limited evidence. This opportunity is based on "
                "one supporting source and should not be treated as validated market-wide demand."
            )
        elif count < 3 or "limited" in strength.lower():
            st.info("Limited evidence. Validate this signal with additional independent sources.")

        with st.expander("View supporting evidence", expanded=(index == 1)):
            render_evidence(evidence)


def render_brief(brief, index):
    title = get_value(brief, "theme", "opportunity", default=f"AI opportunity brief {index}")
    problem = get_value(brief, "problem", default="")
    affected_users = get_value(brief, "who_is_affected", "affected_users", default="")
    why = get_value(brief, "why_it_matters", "why_now", default="")
    product_idea = get_value(brief, "possible_product_idea", "product_angle", "product_idea", default="")
    next_step = get_value(brief, "next_validation_step", "validation_step", default="")
    evidence = get_evidence_items(brief)
    count = evidence_count(brief)

    with st.expander(f"Brief {index}: {title}", expanded=(index == 1)):
        if count <= 1:
            st.warning(
                "Preliminary brief: only one supporting source is attached. "
                "Treat this as a hypothesis to validate, not confirmed demand."
            )

        sections = [
            ("Problem", problem),
            ("Affected users", affected_users),
            ("Why it matters", why),
            ("Possible product idea", product_idea),
            ("Next validation step", next_step),
        ]
        for heading, content in sections:
            if content:
                st.markdown(f"**{heading}**")
                st.write(content)

        st.markdown("**Evidence**")
        render_evidence(evidence)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.25rem;
        font-weight: 750;
        letter-spacing: -0.04em;
        margin-bottom: 0.15rem;
    }
    .sub-header {
        color: #8b949e;
        margin-bottom: 1.4rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.07);
        border: 1px solid rgba(128, 128, 128, 0.16);
        padding: 12px 14px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar: research inputs
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🔎 Signal Hunter")
    st.caption("Discover real-world problems, demand signals and product opportunities.")
    st.divider()

    st.markdown("### Research settings")
    topic = st.text_input(
        "Topic / niche",
        placeholder="e.g. WhatsApp automation for small businesses",
        help="Enter the market, product category or problem area you want to research."
    )

    keywords_text = st.text_area(
        "Optional keywords",
        placeholder="WhatsApp API, workflow automation, customer support",
        help="Separate keywords with commas."
    )

    max_pages = st.slider(
        "Maximum successful pages",
        min_value=25,
        max_value=50,
        value=35,
        step=5,
        help="The assessment requires at least 25 relevant pages across 3 or more permitted domains."
    )

    run_button = st.button(
        "🚀 Run research",
        type="primary",
        use_container_width=True,
        disabled=not bool(topic.strip()),
    )

    st.divider()
    st.caption("Research respects public access restrictions and robots.txt rules.")


# ---------------------------------------------------------
# Main page
# ---------------------------------------------------------
st.markdown('<div class="main-header">AI Web Signal Hunter</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Turn public web discussions into evidence-backed product opportunities.</div>',
    unsafe_allow_html=True
)

if run_button:
    clean_topic = topic.strip()
    keywords = [word.strip() for word in keywords_text.split(",") if word.strip()]

    # Clear previous results only when the user deliberately starts a new run.
    st.session_state.pop("research_result", None)
    st.session_state["research_error"] = None
    st.session_state["research_inputs"] = {
        "topic": clean_topic,
        "keywords": keywords,
        "max_pages": max_pages,
    }

    try:
        with st.spinner(
            "Research is running. Discovering pages, checking access permissions, "
            "scraping content and analyzing signals with AI..."
        ):
            raw_result = run_research(
                clean_topic,
                keywords if keywords else None,
                max_pages
            )
            st.session_state["research_result"] = normalize_result(raw_result)
    except Exception as exc:
        st.session_state["research_error"] = str(exc)


if st.session_state.get("research_error"):
    st.error("The research run could not be completed.")
    st.code(st.session_state["research_error"])
    st.info("Check the terminal for the full traceback. Your existing backend files have not been changed.")

result = st.session_state.get("research_result")

if not result:
    st.info("Enter a topic in the sidebar and select **Run research** to generate your first report.")
    st.markdown("### What this dashboard provides")
    info_cols = st.columns(3)
    info_cols[0].markdown("**1. Discover**\n\nFind relevant public discussions, reviews and technical conversations.")
    info_cols[1].markdown("**2. Analyze**\n\nClassify pain points, buying signals, feature requests and pricing concerns.")
    info_cols[2].markdown("**3. Prioritize**\n\nRank opportunities and inspect the original evidence.")
    st.stop()


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------
crawl = get_crawl_data(result)
pages = get_pages(result)
opportunities = get_opportunities(result)
briefs = get_briefs(result)
inputs = st.session_state.get("research_inputs", {})

topic_name = get_value(crawl, "topic", default=inputs.get("topic", "Research results"))
st.markdown(f"## Research report: {topic_name}")

total_discovered = safe_int(get_value(crawl, "total_discovered", "discovered_count", default=0))
total_scraped = safe_int(get_value(crawl, "total_scraped", "successful_pages", "scraped_count", default=len(as_list(get_value(crawl, "pages", default=[])))))
total_failed = safe_int(get_value(crawl, "total_failed", "failed_count", default=len(as_list(get_value(crawl, "failures", default=[])))))
domains = get_value(crawl, "unique_domains", "total_domains", "domain_count", default=None)
if isinstance(domains, list):
    domain_count = len(domains)
else:
    domain_count = safe_int(domains, 0)

if domain_count == 0:
    page_domains = {
        str(page.get("source_domain"))
        for page in as_list(get_value(crawl, "pages", default=[]))
        if isinstance(page, dict) and page.get("source_domain")
    }
    domain_count = len(page_domains)

analysis_attempts = safe_int(get_value(result, "analysis_api_attempts", "api_call_count", default=0))
analysis_failures = as_list(get_value(result, "analysis_failures", "failed_analyses", default=[]))
if not analysis_failures:
    analysis_failures = as_list(get_value(result, "analysis_errors", default=[]))

metric_cols = st.columns(4)
metric_cols[0].metric("Pages discovered", total_discovered)
metric_cols[1].metric("Pages scraped", total_scraped)
metric_cols[2].metric("Unique domains", domain_count)
metric_cols[3].metric("Scrape failures", total_failed)

metric_cols_2 = st.columns(4)
metric_cols_2[0].metric("Pages analyzed", len(pages))
metric_cols_2[1].metric("Opportunities", len(opportunities))
metric_cols_2[2].metric("AI briefs", len(briefs))
metric_cols_2[3].metric("Analysis API attempts", analysis_attempts if analysis_attempts else "—")

target_reached = get_value(crawl, "target_reached", default=None)
if target_reached is True:
    st.success("The requested successful-page target was reached.")
elif target_reached is False:
    st.warning("The requested successful-page target was not reached. Review the crawl failures below.")

if domain_count and domain_count < 3:
    st.warning("Fewer than 3 unique domains were recorded. The assessment requires coverage across at least 3 permitted domains.")

st.divider()


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab_overview, tab_opportunities, tab_briefs, tab_pages, tab_failures, tab_export = st.tabs([
    "Overview",
    "Opportunities",
    "AI briefs",
    "Analyzed pages",
    "Failures",
    "Export",
])

with tab_overview:
    st.subheader("Signal overview")

    if pages:
        page_df = make_pages_dataframe(pages)
        category_counts = page_df["Category"].fillna("unknown").value_counts()
        left, right = st.columns(2)

        with left:
            st.markdown("**Signals by category**")
            st.bar_chart(category_counts)

        with right:
            st.markdown("**Average AI scores by category**")
            score_columns = ["Relevance", "Urgency", "Confidence"]
            score_df = page_df.groupby("Category")[score_columns].mean().round(1)
            if not score_df.empty:
                st.bar_chart(score_df)

        relevant_count = int((page_df["Category"].str.lower() != "irrelevant").sum())
        irrelevant_count = int((page_df["Category"].str.lower() == "irrelevant").sum())
        summary_cols = st.columns(3)
        summary_cols[0].metric("Relevant signal pages", relevant_count)
        summary_cols[1].metric("Irrelevant pages", irrelevant_count)
        summary_cols[2].metric("Analysis failures", len(analysis_failures))
    else:
        st.info("No successfully analyzed pages were returned for this run.")

    st.markdown("**Opportunity ranking formula**")
    st.code(
        "Opportunity Score = 0.30 × Frequency"
        " + 0.25 × Relevance"
        " + 0.20 × Urgency"
        " + 0.15 × Confidence"
        " + 0.10 × Recency",
        language="text"
    )
    st.caption(
        "This is a prioritization heuristic, not a statistical measure of market size or proof of demand."
    )


with tab_opportunities:
    st.subheader("Ranked product opportunities")

    if not opportunities:
        st.info("No opportunities were generated from the analyzed pages in this run.")
    else:
        categories = sorted({
            str(get_value(item, "category", default="Uncategorized"))
            for item in opportunities
        })
        selected_categories = st.multiselect(
            "Filter by category",
            options=categories,
            default=categories,
            key="opportunity_category_filter",
        )
        filtered_opportunities = [
            item for item in opportunities
            if str(get_value(item, "category", default="Uncategorized")) in selected_categories
        ]
        filtered_opportunities = sorted(
            filtered_opportunities,
            key=lambda item: safe_float(get_value(item, "opportunity_score", "score", default=0)),
            reverse=True
        )

        for index, opportunity in enumerate(filtered_opportunities, start=1):
            render_opportunity_card(opportunity, index)


with tab_briefs:
    st.subheader("AI-generated opportunity briefs")
    st.caption("Briefs are generated from the ranked evidence. Always inspect the source links before drawing conclusions.")

    if not briefs:
        st.info("No AI opportunity briefs were generated for this run.")
    else:
        for index, brief in enumerate(briefs, start=1):
            render_brief(brief, index)


with tab_pages:
    st.subheader("Analyzed page details")

    if not pages:
        st.info("No analyzed page records are available.")
    else:
        page_df = make_pages_dataframe(pages)
        category_options = sorted(page_df["Category"].dropna().astype(str).unique().tolist())
        source_options = sorted(page_df["Source type"].dropna().astype(str).unique().tolist())

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_page_categories = st.multiselect(
                "Category",
                category_options,
                default=category_options,
                key="page_category_filter",
            )
        with filter_col2:
            selected_source_types = st.multiselect(
                "Source type",
                source_options,
                default=source_options,
                key="page_source_filter",
            )
        with filter_col3:
            min_confidence = st.slider(
                "Minimum confidence",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
                key="page_confidence_filter",
            )

        filtered_df = page_df[
            page_df["Category"].astype(str).isin(selected_page_categories)
            & page_df["Source type"].astype(str).isin(selected_source_types)
            & (pd.to_numeric(page_df["Confidence"], errors="coerce").fillna(0) >= min_confidence)
        ]

        st.caption(f"Showing {len(filtered_df)} of {len(page_df)} analyzed pages.")
        st.dataframe(
            filtered_df[[
                "Category", "Title", "Source domain", "Source type",
                "Relevance", "Urgency", "Confidence", "URL"
            ]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Inspect a page**")
        page_titles = [
            f"{row['Title']} — {row['Category']} — {row['Source domain']}"
            for _, row in filtered_df.iterrows()
        ]
        if page_titles:
            selected_title = st.selectbox("Select an analyzed page", page_titles)
            selected_row = filtered_df.iloc[page_titles.index(selected_title)]
            st.markdown(f"**Summary:** {selected_row['Summary']}")
            if selected_row["Supporting excerpt"]:
                st.markdown("**Supporting excerpt:**")
                st.markdown(f"> {selected_row['Supporting excerpt']}")
            if selected_row["Reason"]:
                st.markdown(f"**AI reasoning:** {selected_row['Reason']}")
            render_source_link(selected_row["URL"], "Open original page")


with tab_failures:
    st.subheader("Crawl and analysis failures")
    crawl_failures = as_list(get_value(crawl, "failures", "failed_pages", default=[]))

    if crawl_failures:
        st.markdown("**Pages that could not be scraped**")
        for index, failure in enumerate(crawl_failures, start=1):
            if isinstance(failure, dict):
                url = get_value(failure, "url", "source_url", default="")
                reason = get_value(failure, "reason", "error", "message", default="Reason not provided")
                st.write(f"{index}. {reason}")
                render_source_link(url, "Open failed URL")
            else:
                st.write(f"{index}. {failure}")
    else:
        st.write("No crawl failure details were returned by the pipeline.")
        if total_failed:
            st.caption(f"The pipeline reported {total_failed} scrape failures, but did not include individual failure details.")

    st.divider()
    st.markdown("**Pages that failed AI analysis or validation**")
    if analysis_failures:
        for index, failure in enumerate(analysis_failures, start=1):
            if isinstance(failure, dict):
                title = get_value(failure, "title", default=f"Page {index}")
                url = get_value(failure, "url", default="")
                reason = get_value(failure, "reason", "error", "message", default="Reason not provided")
                st.write(f"**{title}**")
                st.caption(str(reason))
                render_source_link(url, "Open source")
            else:
                st.write(f"{index}. {failure}")
    else:
        st.write("No separate analysis-failure list was returned by the pipeline.")
        st.caption("A page that fails validation may be omitted from analyzed pages. Check the run log for its exact error.")


with tab_export:
    st.subheader("Download research data")

    pages_df = make_pages_dataframe(pages)
    opportunities_df = make_opportunities_dataframe(opportunities)

    col1, col2, col3 = st.columns(3)

    with col1:
        if not pages_df.empty:
            csv_buffer = io.StringIO()
            pages_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "⬇️ Analyzed pages CSV",
                data=csv_buffer.getvalue(),
                file_name="ai_web_signal_hunter_analyzed_pages.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("No analyzed pages CSV available.")

    with col2:
        if not opportunities_df.empty:
            csv_buffer = io.StringIO()
            opportunities_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "⬇️ Opportunities CSV",
                data=csv_buffer.getvalue(),
                file_name="ai_web_signal_hunter_opportunities.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("No opportunities CSV available.")

    with col3:
        json_data = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        st.download_button(
            "⬇️ Full research JSON",
            data=json_data,
            file_name="ai_web_signal_hunter_full_report.json",
            mime="application/json",
            use_container_width=True,
        )

    st.caption("The JSON export contains the full pipeline response, including available evidence and failure details.")

st.divider()
st.caption(
    f"AI Web Signal Hunter · Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')} · "
    "Research findings are exploratory and should be independently validated."
)
