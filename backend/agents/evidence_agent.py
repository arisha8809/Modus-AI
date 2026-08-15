"""
Evidence Agent.

Once findings have been extracted from multiple sources for a sub-question,
this agent looks at them together (not one at a time) and:

  1. Classifies each finding as "corroborated" (matches another source),
     "single_source" (only one source says this), or "contested" (sources
     disagree).
  2. Identifies specific contradiction pairs with a short explanation of what
     disagrees.

This is what the challenge brief calls "Compare Evidence -> Classify Findings
-> Detect Contradictions" -- it only makes sense once you have more than one
source's worth of findings, which is why it runs after extraction for all
sources under a sub-question, not per-source.
"""

from .llm_client import chat_json

SYSTEM_PROMPT = """You are a research evidence-comparison agent working on \
the {domain} industry. You are given a list of findings extracted from \
different sources, all about the same sub-question. Each finding has an id, \
the claim text, and which source url it came from.

Your job:
1. For each finding id, classify it as one of:
   - "corroborated": at least one other finding from a DIFFERENT source \
     supports the same claim
   - "contested": another finding from a DIFFERENT source contradicts it
   - "single_source": no other source addresses this claim either way
2. List contradiction pairs: which finding ids directly disagree with each \
   other, and a one-sentence explanation of the disagreement, framed in \
   {domain}-relevant terms where relevant (e.g. differing figures, \
   differing recommended approaches, differing scope claims).

Return JSON in exactly this shape:
{{
  "classifications": {{"<finding_id>": "corroborated" | "contested" | "single_source", ...}},
  "contradictions": [
    {{"finding_id_a": <id>, "finding_id_b": <id>, "explanation": "<why they disagree>"}}
  ]
}}
"""


def compare_evidence(findings: list[dict], domain: str = "general") -> dict:
    """`findings` is a list of {id, claim, source_url} dicts."""
    if not findings:
        return {"classifications": {}, "contradictions": []}
    if len(findings) == 1:
        return {"classifications": {str(findings[0]["id"]): "single_source"}, "contradictions": []}

    listing = "\n".join(
        f"id={f['id']} | source={f['source_url']} | claim: {f['claim']}" for f in findings
    )
    result = chat_json(
        system_prompt=SYSTEM_PROMPT.format(domain=domain or "general"),
        user_prompt=f"Findings:\n{listing}",
    )
    return {
        "classifications": result.get("classifications", {}),
        "contradictions": result.get("contradictions", []),
    }
