from __future__ import annotations

import tiktoken

# Cost per 1M tokens (input, output) — update as pricing changes
_COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "gemini-1.5-pro": (3.50, 10.50),
}
_DEFAULT_COST = (5.00, 15.00)


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    input_cost, output_cost = _COST_TABLE.get(model, _DEFAULT_COST)
    return (input_tokens * input_cost + output_tokens * output_cost) / 1_000_000
