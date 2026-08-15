"""
Synthesis Agent.

Final stage of the pipeline. Given the original research question and all
findings collected + classified across every sub-question, this agent writes
the actual conclusions -- and for each one, names exactly which finding ids
support it. That link is what gets stored in the `conclusion_findings` join
table, which is what makes every conclusion traceable back to real sources
rather than being a plausible-sounding LLM summary.
"""

from .llm_client import chat_json

SYSTEM_PROMPT = """You are a research synthesis agent working on the {domain} \
industry. You are given the original research question and a list of \
findings (each with an id, its evidence classification, and the claim text) \
gathered from web research.

Write 3 to 6 clear, SPECIFIC conclusions that answer the research question, \
using ONLY the findings provided -- do not introduce outside knowledge. \
Prefer findings classified "corroborated" as stronger evidence; note where a \
conclusion rests on a "contested" or "single_source" finding so the reader \
knows the confidence level. Frame conclusions in terms that would make sense \
to a {domain} business stakeholder, not generic AI-hype language.

Strict rules:
- Each conclusion must be about ONE specific theme (e.g. inventory \
  forecasting, customer personalization, supply chain visibility) -- not a \
  broad restatement of everything found.
- Each conclusion must cite AT MOST 6 supporting finding ids -- the ones \
  that most directly and specifically support that exact claim. If more than \
  6 findings relate to a theme, pick the strongest 6, don't cite them all.
- Do NOT write a final "overall" or "in summary" conclusion that restates the \
  other conclusions combined. Every conclusion must be a distinct, specific \
  claim standing on its own -- if you're tempted to summarize everything \
  together, that means you should stop, not write one more conclusion.
- Never cite the same finding id in more than 2 different conclusions --  if \
  a finding seems to support several conclusions, pick the single best fit.

Return JSON in exactly this shape:
{{
  "conclusions": [
    {{"text": "<specific conclusion statement>", "supporting_finding_ids": [<id>, <id>, ...]}}
  ]
}}
"""


def synthesize(research_question: str, findings: list[dict], domain: str = "general") -> list[dict]:
    """`findings` is a list of {id, claim, classification} dicts."""
    if not findings:
        return []
    listing = "\n".join(
        f"id={f['id']} | classification={f['classification']} | claim: {f['claim']}"
        for f in findings
    )
    result = chat_json(
        system_prompt=SYSTEM_PROMPT.format(domain=domain or "general"),
        user_prompt=f"Research question: {research_question}\n\nFindings:\n{listing}",
    )
    conclusions = result.get("conclusions", [])

    # Hard backstop, independent of the LLM actually following the prompt's
    # rules: never let a conclusion cite more than MAX_FINDINGS_PER_CONCLUSION
    # findings. This is what directly prevents a repeat of a "catch-all"
    # conclusion citing every finding from the run.
    MAX_FINDINGS_PER_CONCLUSION = 6
    for c in conclusions:
        ids = c.get("supporting_finding_ids", [])
        if len(ids) > MAX_FINDINGS_PER_CONCLUSION:
            c["supporting_finding_ids"] = ids[:MAX_FINDINGS_PER_CONCLUSION]

    return conclusions
