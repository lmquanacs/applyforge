import os
import concurrent.futures
import anthropic
import click
from codelens.core.discovery import discover
from codelens.core.chunking import collect_chunks
from codelens.agents.worker_agent import WorkerAgent
from codelens.output.markdown_builder import build_markdown


class CoordinatorAgent:
    def __init__(self, config: dict, verbose: bool = False, dry_run: bool = False):
        self.config = config
        self.verbose = verbose
        self.dry_run = dry_run
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.worker = WorkerAgent(config=config, verbose=verbose)
        self.coord_config = config["agents"]["coordinator"]

    def run(self, path: str):
        if self.verbose:
            click.echo("[Coordinator] Phase 1 & 2: Discovery...")
        context = discover(path)
        hint = self.config.get("project_hint") or context["hint"]
        context["hint"] = hint

        if self.verbose:
            click.echo(f"[Coordinator] Phase 3: Collecting source files (hint={hint})...")
        chunks = collect_chunks(path, hint, self.config["ignore_patterns"])

        if self.dry_run:
            total_tokens = sum(self.worker.estimate_tokens(c) for c in chunks)
            click.echo(f"[Dry Run] Files to process: {len(chunks)}")
            click.echo(f"[Dry Run] Estimated tokens: ~{total_tokens:,}")
            return

        if self.verbose:
            click.echo(f"[Coordinator] Dispatching {len(chunks)} files to workers...")

        max_workers = self.config["agents"]["worker"].get("max_concurrent_workers", 5)
        summaries = self._run_workers(chunks, hint, max_workers)

        if self.verbose:
            click.echo("[Coordinator] Phase 4: Aggregating report...")
        final_report = self._aggregate(context, summaries)

        output_path = self.config.get("output_file", "project_overview.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_report)

        click.echo(f"Report written to: {output_path}")

    def _run_workers(self, chunks, hint: str, max_workers: int) -> list:
        summaries = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.worker.summarize, chunk, hint): chunk for chunk in chunks}
            for future in concurrent.futures.as_completed(futures):
                chunk = futures[future]
                try:
                    summary = future.result()
                    summaries.append({"path": chunk.path, "summary": summary})
                except Exception as e:
                    if self.verbose:
                        click.echo(f"  [Worker Error] {chunk.path}: {e}")
        return summaries

    def _aggregate(self, context: dict, summaries: list) -> str:
        summaries_text = "\n\n".join(
            f"### {s['path']}\n{s['summary']}" for s in summaries
        )

        readme_section = f"README:\n{context['readme_content']}\n\n" if context.get("readme_content") else ""
        config_section = "\n\n".join(
            f"{name}:\n```\n{content[:3000]}\n```"
            for name, content in context.get("config_files", {}).items()
        )

        prompt = f"""You are a senior software architect. Based on the following project context, generate a comprehensive project overview report in Markdown.

Project hint: {context['hint']}

{readme_section}{config_section}

Worker Summaries:
{summaries_text[:30000]}

Generate the report with these sections:
1. Project Title & Executive Summary
2. Tech Stack & Dependencies
3. Application Architecture
4. Core Components (API Endpoints, Business Services, Data Models)
5. Getting Started
6. Missing Pieces / Analysis
"""

        response = self.client.messages.create(
            model=self.coord_config["model"],
            max_tokens=4096,
            temperature=self.coord_config["temperature"],
            system="You are a senior software architect generating project documentation.",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
