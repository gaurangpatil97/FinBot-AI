from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict, Optional
from loguru import logger

# Context-local token usage dictionary
token_usage_var: ContextVar[Optional[Dict[str, int]]] = ContextVar("token_usage_var", default=None)

def init_token_tracker() -> Dict[str, int]:
    """Initialize token tracker in the current context."""
    tracker = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
    token_usage_var.set(tracker)
    return tracker

def record_token_usage(response: Any) -> None:
    """Extract and accumulate token usage from an OpenAI response."""
    try:
        usage = getattr(response, "usage", None)
        if usage:
            curr = token_usage_var.get()
            if curr is not None:
                curr["prompt_tokens"] += getattr(usage, "prompt_tokens", 0)
                curr["completion_tokens"] += getattr(usage, "completion_tokens", 0)
                curr["total_tokens"] += getattr(usage, "total_tokens", 0)
    except Exception as e:
        logger.warning(f"Failed to record token usage: {e}")

def get_token_usage() -> Optional[Dict[str, int]]:
    """Retrieve the accumulated token usage for the current context."""
    return token_usage_var.get()
