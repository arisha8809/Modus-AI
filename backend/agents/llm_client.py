"""Single entry point for all LLM calls.

All agents continue to use the Groq API through this module. The client
handles Groq model retirement or account-level model access changes by trying
another supported Groq model; it never switches to another provider.
"""

import json
import os

from groq import Groq

DEFAULT_MODEL = "llama-3.1-8b-instant"
configured_model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
# Older local .env files may still contain the retired identifier.
MODEL_NAME = DEFAULT_MODEL if configured_model == "llama-3.3-70b-versatile" else configured_model
FALLBACK_MODELS = ["llama-3.1-8b-instant", "openai/gpt-oss-20b"]

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


def _completion(**kwargs):
    """Call Groq and recover from a model-access/deprecation error."""
    global MODEL_NAME
    client = _get_client()
    candidates = [MODEL_NAME] + [model for model in FALLBACK_MODELS if model != MODEL_NAME]
    last_error = None
    for model in candidates:
        try:
            response = client.chat.completions.create(model=model, **kwargs)
            MODEL_NAME = model
            return response
        except Exception as exc:
            last_error = exc
            status_code = getattr(exc, "status_code", None)
            message = str(exc).lower()
            is_model_error = status_code == 404 or "model" in message or "not found" in message
            if not is_model_error:
                raise
    raise last_error


def chat_text(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """Plain text completion through Groq."""
    response = _completion(
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    """JSON completion through Groq for structured agent outputs."""
    response = _completion(
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
        cleaned = raw.strip("`").replace("json\n", "", 1)
        return json.loads(cleaned)
