from __future__ import annotations

import typer
import litellm
from litellm import completion

from career_ai.config import Config
from career_ai.llm.tokens import count_tokens, estimate_cost
from career_ai.utils.logging import console, log_usage

litellm.drop_params = True


def _build_messages(system: str, user: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_llm(
    system_prompt: str,
    user_prompt: str,
    config: Config,
    model: str | None = None,
    dry_run: bool = False,
) -> str:
    target_model = model or config.model.default
    full_prompt = system_prompt + "\n" + user_prompt
    input_tokens = count_tokens(full_prompt, target_model)
    estimated_cost = estimate_cost(input_tokens, config.tokens.max_output_limit, target_model)

    if input_tokens > config.tokens.max_input_limit:
        console.print(
            f"[bold red]Aborted:[/] Input is {input_tokens} tokens, exceeds limit of "
            f"{config.tokens.max_input_limit}."
        )
        raise typer.Exit(1)

    if estimated_cost > config.tokens.warn_cost_threshold:
        console.print(
            f"[bold yellow]Warning:[/] Estimated cost ${estimated_cost:.4f} exceeds "
            f"threshold ${config.tokens.warn_cost_threshold:.2f}."
        )

    if dry_run:
        console.rule("[bold cyan]Dry Run[/]")
        console.print(f"[bold]Target Model:[/]    {target_model}")
        console.print(f"[bold]Input Tokens:[/]    {input_tokens}")
        console.print(f"[bold]Estimated Cost:[/]  ${estimated_cost:.4f}")
        console.rule("[bold cyan]Prompt Payload[/]")
        console.print(full_prompt)
        raise typer.Exit(0)

    messages = _build_messages(system_prompt, user_prompt)

    try:
        response = completion(
            model=target_model,
            messages=messages,
            temperature=config.model.temperature,
            max_tokens=config.tokens.max_output_limit,
        )
    except Exception:
        console.print(f"[yellow]Primary model failed, falling back to {config.model.fallback}[/]")
        response = completion(
            model=config.model.fallback,
            messages=messages,
            temperature=config.model.temperature,
            max_tokens=config.tokens.max_output_limit,
        )

    usage = response.usage
    actual_cost = estimate_cost(usage.prompt_tokens, usage.completion_tokens, target_model)

    if config.app.log_usage:
        log_usage(
            model=target_model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost=actual_cost,
            db_path=config.usage_db,
        )

    return response.choices[0].message.content
