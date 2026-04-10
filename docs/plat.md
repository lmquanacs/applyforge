# Product Specification: CodeLens CLI (Project Scanner)

## 1. Overview

CodeLens CLI is a command-line tool that intelligently scans local software project directories and generates a comprehensive summary report in Markdown format. To handle large codebases without exceeding token context limits, the tool uses a hierarchical multi-agent LLM architecture powered by Anthropic Claude.

**Initial Milestone:** The tool is initially specialised and optimised for Java Spring Boot projects. By providing a `--hint`, the scanner bypasses generic discovery and applies targeted Spring heuristics.

## 2. Objectives

- Provide automated, high-level understanding of unknown or large codebases.
- Prevent context-window exhaustion via a hierarchical Coordinator-Worker LLM architecture.
- Minimise API cost by compressing source files into token-efficient skeletons before sending to LLMs.
- Allow model configuration via `codelens.config.yaml` or CLI flags.
- Output a clean, readable Markdown file covering project purpose, tech stack, architecture, and key components.

## 3. Core Architecture: Multi-Agent System

```
CLI (cli.py)
 └── CoordinatorAgent
      ├── discovery.py       Phase 1 & 2: root scan + README ingestion
      ├── chunking.py        Phase 3: file collection + prioritisation
      │    └── compressor.py Pre-processing: compress source → skeleton
      └── WorkerAgent ×N     Concurrent per-file summarisation
           └── Phase 4: Coordinator aggregates → final report
```

- **Coordinator Agent** (`claude-haiku-4-5` by default for testing, swap to `claude-opus-4-5` / `claude-sonnet-4-5` for production): orchestrates all phases, aggregates worker summaries, generates the final report.
- **Worker Agents** (`claude-haiku-4-5`): receive compressed file skeletons and return structured per-file summaries. Run concurrently via `ThreadPoolExecutor`.

## 4. Execution Workflow

### Phase 1 & 2: Discovery & Documentation Ingestion

- Reads root directory entries.
- Detects project type via heuristics:
  - `pom.xml` / `build.gradle` / `mvnw` / `gradlew` → `spring-boot`
  - `package.json` → `node`
  - `manage.py` → `django`
  - fallback → `generic`
- Reads `README.md` (or first `.md` found in root / `docs/`).
- Reads `pom.xml`, `build.gradle`, `application.yml`, `application.properties` if present.

### Phase 3: Source Code Collection & Compression

- For `spring-boot`: targets `src/main/java` only (test files excluded).
- For `generic`: walks root for `.py`, `.js`, `.ts`, `.java`, `.go`, `.rb`.
- Files are **compressed** by `compressor.py` before chunking:
  - **Java**: retains package, collapsed imports, class declaration, field declarations, method signatures — strips all method bodies and comments. Typically reduces file size by ~60–70%.
  - **Python**: retains imports, class/def signatures, and docstrings — strips all function bodies.
  - **Generic**: strips blank lines and line comments only.
- Files are prioritised by Spring stereotype annotation count (`@RestController` > `@Service` > `@Entity` etc.) so high-signal files are processed first.
- Secret files (`.env`, `*.pem`, `*.key`, `*secret*`, `*credential*`) are hard-excluded.

### Phase 4: Aggregation and Reporting

- Coordinator receives all worker summaries.
- Synthesises root context, README, config files, and summaries into a final Markdown report.
- Output sections: Executive Summary, Tech Stack, Architecture, Core Components, Getting Started, Missing Pieces / Analysis.
- Report written to `output_file` (default: `project_overview.md`).

## 5. Source Compression (`core/compressor.py`)

The compressor is the primary cost-reduction mechanism. It transforms raw source into a readable but token-efficient skeleton that preserves all structural signal an LLM needs.

**Java example — input (~250 lines):**
```java
public class Gateway {
    private final OkHttpClient okHttpClient;
    ...
    public void start() {
        // 80 lines of socket loop
    }
    private void handleClient(Socket client, ...) {
        // 60 lines
    }
}
```

**Java example — compressed output (~20 lines):**
```java
package com.vps.auth.gateway;

import com.google.gson.*;
import com.vps.auth.*;
import okhttp3.*;

public class Gateway {
  private final OkHttpClient okHttpClient;
  private final PanHandler panHandler;
  private final ServerSocket serverSocket;
  public Gateway(Integer port, String panserverUrl, ...) {}
  public void start() {}
  private void handleClient(Socket client, String clientName, String requestId) {}
  private static Map<String, String> parseClientMessage(Socket client) throws IOException;
}
```

## 6. Environment Setup

### API Key

```bash
# .env (in codelens-cli/)
ANTHROPIC_API_KEY=sk-ant-...
```

The tool loads this automatically via `python-dotenv`.

### Configuration File

`codelens.config.yaml` in the working directory:

```yaml
output_file: "project_overview.md"
project_hint: null  # auto-detect; override with e.g. "spring-boot"
ignore_patterns:
  - "target/**"
  - "build/**"
  - ".idea/**"
  - ".git/**"
  - "venv/**"
  - "__pycache__/**"

agents:
  coordinator:
    provider: "anthropic"
    model: "claude-haiku-4-5"      # swap to claude-opus-4-5 for production quality
    temperature: 0.2

  worker:
    provider: "anthropic"
    model: "claude-haiku-4-5"
    temperature: 0.1
    max_concurrent_workers: 5
```

## 7. Command Line Interface

```bash
codelens scan [OPTIONS] <PATH>
```

**Examples:**
```bash
codelens scan .
codelens scan /path/to/repo --hint spring-boot --verbose
codelens scan /path/to/repo --hint spring-boot --dry-run   # estimate tokens before spending
codelens scan /path/to/repo -c my-config.yaml -o report.md
```

**Flags:**
- `-c, --config` — path to `codelens.config.yaml`
- `-o, --output` — output markdown file path
- `--hint` — framework hint (`spring-boot`, `django`, `node`, `generic`)
- `-v, --verbose` — stream coordinator and worker logs
- `--dry-run` — print file count and estimated token usage, no API calls

## 8. Expected Markdown Output Structure

1. Project Title & Executive Summary
2. Tech Stack & Dependencies
3. Application Architecture
4. Core Components — API Endpoints, Business Services, Data Models
5. Getting Started
6. Missing Pieces / Analysis

## 9. Cost Optimisation

| Lever | Setting | Effect |
|-------|---------|--------|
| Source compression | `compressor.py` | ~60–70% token reduction per file |
| Worker model | `claude-haiku-4-5` | Cheapest Anthropic model |
| Coordinator model | `claude-haiku-4-5` (test) / `claude-opus-4-5` (prod) | Balance cost vs quality |
| Worker `max_tokens` | 512 | Caps per-file summary length |
| Coordinator `max_tokens` | 2048 | Caps final report length |
| Summaries fed to coordinator | 15,000 chars max | Prevents coordinator context overflow |
| `--dry-run` | CLI flag | Estimate cost before committing |

## 10. Project Structure

```
codelens-cli/
├── codelens/
│   ├── cli.py                      # Click entry point
│   ├── config/
│   │   └── parser.py               # YAML config loader with dotenv + defaults
│   ├── core/
│   │   ├── discovery.py            # Phase 1 & 2: root scan, hint detection, README
│   │   ├── chunking.py             # Phase 3: file collection, prioritisation
│   │   └── compressor.py           # Source → token-efficient skeleton
│   ├── agents/
│   │   ├── coordinator_agent.py    # Orchestration + final aggregation (Claude)
│   │   └── worker_agent.py         # Per-file summarisation (Claude)
│   └── output/
│       └── markdown_builder.py     # Pass-through, reserved for templating
├── tests/
│   ├── test_discovery.py
│   └── test_agents.py
├── codelens.config.yaml
├── requirements.txt                # anthropic, click, pyyaml, python-dotenv
├── setup.py
├── Makefile
├── .env.example
└── .gitignore
```

## 11. Makefile

All commands use the local `venv/bin/` prefix — no global activation required.

```bash
make venv      # python3 -m venv venv
make install   # venv/bin/pip install -e .
make dev       # install + dev deps (pytest, black, flake8, isort)
make test      # pytest with coverage
make lint      # flake8
make format    # black + isort
make run       # codelens scan . --verbose
make clean     # remove build artifacts
make build     # sdist + bdist_wheel
```

## 12. Quick Start

```bash
git clone https://github.com/lmquanacs/applyforge.git
cd applyforge/codelens-cli

make venv
cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY

make install

# dry run first
codelens scan /path/to/project --hint spring-boot --dry-run

# full scan
codelens scan /path/to/project --hint spring-boot --verbose
```

## 13. Edge Cases & Considerations

- **Token Limits:** If worker summaries exceed the coordinator's context, a middle tier of Sub-Coordinators (Tree of Thought) should be implemented. Currently mitigated by the 15,000-char summary cap.
- **Security:** Secret files (`.env`, `*.pem`, `*.key`, `*secret*`, `*credential*`) are hard-excluded from chunking. Config files like `application.yml` are read but capped at 3,000 chars.
- **Cost Management:** Always use `--dry-run` on unknown repos before a full scan. Use `claude-haiku-4-5` for both agents during development.
- **Python 3.9 compatibility:** All type hints use `typing.List` / `typing.Optional` — no `X | Y` union syntax.
