"""
Classifier / Planner Agent.

This is the agent that makes the whole app domain-agnostic. It does NOT
assume the topic is retail, or manufacturing, or media -- it reads whatever
research question comes in (including one an evaluator types live) and:

  1. Identifies the industry/domain the question is about.
  2. Breaks the question into 3-5 focused sub-questions that are easier to
     search and extract findings for individually than one broad question.

Every downstream agent (search, extraction, evidence, synthesis) is generic
and just operates on whatever domain + sub-questions this agent produces.
"""

from .llm_client import chat_json

SYSTEM_PROMPT = """You are a research planning agent for an enterprise AI \
research system. Given a broad research question about any industry, you:

1. Identify the industry/domain the question is about (e.g. "retail", \
"manufacturing", "healthcare", "media & entertainment", "banking", etc.)
2. Break the question into 3 to 5 focused, independently-searchable \
sub-questions that together would let a researcher answer the original \
question thoroughly.

Return JSON in exactly this shape:
{
  "domain": "<short industry label>",
  "sub_questions": ["<sub-question 1>", "<sub-question 2>", ...]
}
"""


def classify_and_plan(research_question: str) -> dict:
    result = chat_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Research question: {research_question}",
    )
    # Defensive defaults in case the model returns something malformed
    domain = result.get("domain", "general")
    sub_questions = result.get("sub_questions") or [research_question]
    return {"domain": domain, "sub_questions": sub_questions[:5]}
