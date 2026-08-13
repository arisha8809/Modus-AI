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

SYSTEM_PROMPT = """You are a research synthesis agent. You are given the \
original research question and a list of findings (each with an id, its \
evidence classification, and the claim text) gathered from web research.

Write 3 to 6 clear conclusions that answer the research question, using ONLY \
the findings provided -- do not introduce outside knowledge. Prefer findings \
classified "corroborated" as stronger evidence; note where a conclusion \
rests on a "contested" or "single_source" finding so the reader knows the \
confidence level. For every conclusion, list the exact finding ids it is \
based on.

Return JSON in exactly this shape:
{
  "conclusions": [
    {"text": "<conclusion statement>", "supporting_finding_ids": [<id>, <id>, ...]}
  ]
}
"""


def synthesize(research_question: str, findings: list[dict]) -> list[dict]:
    """`findings` is a list of {id, claim, classification} dicts."""
    if not findings:
        return []
    listing = "\n".join(
        f"id={f['id']} | classification={f['classification']} | claim: {f['claim']}"
        for f in findings
    )
    result = chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Research question: {research_question}\n\nFindings:\n{listing}",
    )
    return result.get("conclusions", [])
