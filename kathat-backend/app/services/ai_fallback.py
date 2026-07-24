"""
Shared LLM fallback chain used by both the hot-lead summarizer (worker.py)
and the AI Sales Agent endpoint (routers/agent.py). Implemented over the raw
HTTP APIs directly (no SDK dependency) to keep the backend lean.
"""
import httpx

from ..config import settings

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


async def _try_openai(model: str, system: str | None, messages: list[dict]) -> str | None:
    if not settings.openai_api_key:
        return None
    payload_messages = ([{"role": "system", "content": system}] if system else []) + messages
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                OPENAI_URL, headers=headers,
                json={"model": model, "messages": payload_messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            print(f"OpenAI ({model}) failed: {e}")
            return None


async def _try_anthropic(system: str | None, messages: list[dict]) -> str | None:
    if not settings.anthropic_api_key:
        return None
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {"model": "claude-3-5-sonnet-20241022", "max_tokens": 400, "messages": messages}
    if system:
        body["system"] = system
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            print(f"Anthropic failed: {e}")
            return None


async def generate_with_fallback(messages: list[dict], system: str | None = None) -> str | None:
    """Try GPT-4o, fall back to Claude 3.5 Sonnet, fall back to GPT-3.5-Turbo.
    Returns None (never raises) if every provider fails, so a missing AI
    reply never takes down the lead pipeline or the chat endpoint."""
    for attempt in (
        lambda: _try_openai("gpt-4o", system, messages),
        lambda: _try_anthropic(system, messages),
        lambda: _try_openai("gpt-3.5-turbo", system, messages),
    ):
        result = await attempt()
        if result:
            return result
    return None
