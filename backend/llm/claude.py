"""Claude API integration for the Personal Productivity Coach."""

import json
import logging
from typing import Type, TypeVar

from pydantic import BaseModel

from backend.config import ANTHROPIC_API_KEY, MODEL_MAP

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def call_structured(stage: str, system: str, user_message: str,
                    output_model: Type[T], max_tokens: int = 1024) -> T:
    """Call Claude with structured output parsing via Pydantic."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model = MODEL_MAP.get(stage, "claude-sonnet-4-5-20250514")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()

    # Extract JSON from response
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    return output_model.model_validate(data)


def call_chat(system: str, messages: list[dict], tools: list[dict] = None,
              max_tokens: int = 4096) -> dict:
    """Call Claude for chat with optional tool_use."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    model = MODEL_MAP.get("chat", "claude-sonnet-4-5-20250514")

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    response = client.messages.create(**kwargs)

    return {
        "content": response.content,
        "stop_reason": response.stop_reason,
        "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
    }
