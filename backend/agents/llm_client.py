"""
Single entry point for all LLM calls.

Every agent calls `chat_json()` or `chat_text()` from this module instead of
hitting an SDK directly. That means the whole app depends on Groq's free-tier
API through exactly one file -- if Groq ever becomes unavailable or paid,
swapping to another OpenAI-compatible free provider (e.g. OpenRouter) or a
local Ollama model only requires editing this file, nothing in the agents
themselves. This is the direct answer to the challenge's "what happens if
this service becomes paid or unavailable?" requirement.

Model used: llama-3.3-70b-versatile (open-weight Llama model, served free by
Groq). Swap MODEL_NAME below to change it.
"""

import os
import json
from groq import Groq

MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
                "and put it in your .env file (see .env.example)."
            )
        _client = Groq(api_key=api_key)
    return _client


def chat_text(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """Plain text completion."""
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    """Completion constrained to return valid JSON. Used by every agent that
    needs structured output (classification, extraction, etc.) rather than
    free-form prose, so results can actually be stored and queried."""
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt + "\n\nRespond ONLY with valid JSON."},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Best-effort recovery if the model wraps JSON in ```fences```
        cleaned = raw.strip("`").replace("json\n", "", 1)
        return json.loads(cleaned)
