"""Extraction Agent.

Takes the raw text of one fetched source and pulls out structured findings
relevant to the sub-question. It also identifies explicitly dated milestones
so the application can build a source-backed market or technology timeline.
"""

from .llm_client import chat_json

SYSTEM_PROMPT = """You are a research extraction agent working on the {domain} \
industry. Given the text of a web page and a research sub-question, extract \
the distinct factual claims in the page that are relevant to the sub-question. \
Ignore boilerplate, navigation text, and anything irrelevant to the question. \
Prioritize claims that are specific and meaningful within a {domain} context \
(concrete numbers, named technologies, named processes) over generic \
statements that could apply to any industry.

For each claim, also give a short supporting detail (specifics, numbers, or \
context from the text that back up the claim).

Also identify up to 3 major, source-backed timeline events from the page. An
event must have an explicit calendar date or year in the page text. Do not
invent a date from the retrieval date, page URL, or general knowledge. Prefer
meaningful launches, regulatory changes, market shocks, major deployments,
company announcements, scientific breakthroughs, or other developments that
changed the {domain} landscape.

For each event, return:
- event_date: the exact date or year stated by the source, such as "2023-09-01" or "2023"
- title: a concise milestone title
- description: what happened and why it matters, using only the page text
- event_type: one of "launch", "regulation", "market_event", "company_move", "breakthrough", "adoption", "risk_event", or "milestone"
- impact_level: "high", "medium", or "low" as a research-priority judgement
- impact_rationale: one short sentence explaining the selected impact level from the source evidence

Return JSON in exactly this shape:
{{
  "findings": [
    {{"claim": "<concise factual claim>", "detail": "<supporting detail from the text>"}}
  ],
  "timeline_events": [
    {{"event_date": "<explicit date or year>", "title": "<milestone>", "description": "<source-backed significance>", "event_type": "<type>", "impact_level": "<high|medium|low>", "impact_rationale": "<why>"}}
  ]
}}

If the page has nothing relevant, return {{"findings": [], "timeline_events": []}}.
Extract at most 5 findings and 3 timeline events per page.
"""


def extract_findings(sub_question: str, page_text: str, domain: str = "general") -> dict:
    """Return structured claims and dated timeline events from one source."""
    if not page_text or not page_text.strip():
        return {"findings": [], "timeline_events": []}
    result = chat_json(
        system_prompt=SYSTEM_PROMPT.format(domain=domain or "general"),
        user_prompt=f"Sub-question: {sub_question}\n\nPage text:\n{page_text}",
    )
    return {
        "findings": result.get("findings", []),
        "timeline_events": result.get("timeline_events", []),
    }
