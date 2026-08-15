"""
Extraction Agent.

Takes the raw text of one fetched source and pulls out structured findings
relevant to the sub-question it was found for -- not a summary, but discrete
claims that can be individually stored, compared against other sources, and
cited. This is the difference between "the app read some pages" and "the app
built a queryable knowledge base."
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

Return JSON in exactly this shape:
{{
  "findings": [
    {{"claim": "<concise factual claim>", "detail": "<supporting detail from the text>"}},
    ...
  ]
}}

If the page has nothing relevant, return {{"findings": []}}. Extract at most 5 \
findings per page -- pick the most substantive ones.
"""


def extract_findings(sub_question: str, page_text: str, domain: str = "general") -> list[dict]:
    if not page_text or not page_text.strip():
        return []
    result = chat_json(
        system_prompt=SYSTEM_PROMPT.format(domain=domain or "general"),
        user_prompt=f"Sub-question: {sub_question}\n\nPage text:\n{page_text}",
    )
    return result.get("findings", [])
