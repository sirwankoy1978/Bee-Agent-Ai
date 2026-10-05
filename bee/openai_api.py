"""Direct access to the public OpenAI API for verification and utilities.

The agent itself talks to OpenAI through Agno's `OpenAIChat` / `OpenAIResponses`
model classes (which wrap the official `openai` SDK). This module adds
self-checks that use the raw SDK, so you can validate the key, list the models
your account can use, and measure latency before wiring anything to Telegram.
"""

from __future__ import annotations

from typing import Optional

from openai import OpenAI

from bee.config import Settings


def get_client(settings: Settings, base_url: Optional[str] = None) -> OpenAI:
    """Sync OpenAI SDK client bound to the configured key."""
    return OpenAI(api_key=settings.openai_api_key, base_url=base_url)


def list_models(settings: Settings) -> list[str]:
    client = get_client(settings)
    return sorted(m.id for m in client.models.list().data)


def check_model_available(settings: Settings) -> dict:
    """Return a report about the configured model against the live API."""
    client = get_client(settings)
    ids = sorted(m.id for m in client.models.list().data)
    usable = [i for i in ids if i.startswith(("gpt-5", "gpt-4o", "o3", "o4"))]
    return {
        "configured_model": settings.openai_model,
        "model_configured_exists": settings.openai_model in ids,
        "openai_models_usable_for_agent": usable,
        "image_models": [i for i in ids if i.startswith("gpt-image") or "image" in i],
        "total_models": len(ids),
    }


def ping(settings: Settings, prompt: str = "Reply with exactly: OK") -> dict:
    """One-shot completion through the endpoint the agent will actually use."""
    client = get_client(settings)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
    )
    return {
        "reply": response.choices[0].message.content,
        "model": response.model,
        "usage": response.usage.model_dump() if response.usage else None,
    }
