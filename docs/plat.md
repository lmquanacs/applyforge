# Product Specification: CodeLens CLI (Project Scanner)

## 1. Overview

CodeLens CLI is a command-line tool designed to intelligently scan local software project directories and generate a comprehensive summary report in Markdown (.md) format. To handle large codebases without exceeding token context limits, the tool utilizes a configurable multi-agent Large Language Model (LLM) architecture.

**Initial Milestone:** The tool is initially specialized and optimized for Java Spring Boot projects. By providing a "project hint," the scanner can bypass generic discovery phases and immediately apply targeted heuristics for Spring architecture.

## 2. Objectives

- Provide an automated, high-level understanding of unknown or large codebases.
- Prevent context-window exhaustion by utilizing a hierarchical "Coordinator-Worker" LLM architecture. We recommend building this using orchestration frameworks like CrewAI, LangGraph, or Microsoft AutoGen to manage agent state and task delegation efficiently.
- Allow users to configure which LLM models are used for specific tasks to optimize cost and performance. For example, using a cheaper, faster model (like Claude 3 Haiku or GPT-4o-mini) for simple, repetitive jobs such as reading individual source files, extracting basic syntax, and summarizing local functions. Conversely, an expensive, highly-capable model (like GPT-4o or Claude 3.5 Sonnet) is reserved for complex jobs like overall architectural analysis, resolving conflicting information, and generating the final cohesive report.
- Output a clean, readable Markdown file containing project purpose, tech stack, architecture, and key components.

## 3. Core Architecture: Multi-Agent System

The tool operates using a hierarchical agent architecture to ensure "smart" scanning:

- **The Coordinator Agent (Main LLM):** Acts as the project manager. It analyzes the root directory, reviews high-level documentation, decides which source code directories need deeper inspection, and compiles the final report.
- **The Worker Agents (Sub-LLMs):** Act as individual code reviewers. The Coordinator delegates specific files or folders to the Workers. The Workers read the code, summarize the functionality, and return a condensed report back to the Coordinator.

## 4. Execution Workflow

The CLI will execute the scan in the following sequential phases:

### Phase 1: Context & Discovery (Root Scanning)

- **Action:** The tool reads the names of the files and folders in the root directory.
- **Heuristics (Spring Boot Focus):** It actively searches for pom.xml (Maven) or build.gradle (Gradle), mvnw/gradlew wrappers, and the src/main/resources/application.properties or application.yml files.
- **Goal:** The Coordinator Agent uses this list to immediately verify the project type and extract core dependencies (e.g., Spring Data JPA, Spring Security, Spring Web).

### Phase 2: Documentation Ingestion

- **Action:** The tool searches specifically for README.md in the root directory.
- **Fallback:** If README.md is missing, the tool globs for other Markdown files (*.md) in the root or a /docs directory.
- **Goal:** The Coordinator Agent reads these files to understand the stated purpose, usage instructions, and business logic of the application.

### Phase 3: Source Code Deep Dive (Spring Boot Optimized)

- **Action:** Based on the Spring Boot hint, the tool bypasses generic folder scanning and immediately targets src/main/java and src/main/resources.
- **Delegation:** The tool chunks the Java files. It specifically prioritizes files containing Spring stereotypes:
  - @SpringBootApplication (Entry Point)
  - @RestController / @Controller (API layer)
  - @Service (Business logic layer)
  - @Repository (Data access layer)
  - @Entity (Data models)
  - @Configuration (App configuration)
- **Execution:** Worker Agents are spun up concurrently. They are prompted with the Spring Boot context to ensure they extract relevant data (e.g., "Extract all REST API endpoints from this Controller file").
- **Goal:** Workers return domain-specific summaries back to the Coordinator.

### Phase 4: Aggregation and Reporting

- **Action:** The Coordinator Agent receives all summaries from the Worker Agents.
- **Execution:** The Coordinator synthesizes the root context, the documentation, and the Worker code summaries into a cohesive narrative.
- **Output:** Generates the final {project_name}_overview.md file.

## 5. Environment Setup

### API Key Configuration

The tool requires API keys for LLM providers. Set them as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Google AI
export GOOGLE_API_KEY="..."
```

**Recommended approach:** Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

The tool will automatically load these using `python-dotenv`.

### Configuration File

The tool will rely on a codelens.config.yaml file (or CLI flags) to allow model swapping and project hints.

```yaml
# Example Configuration
output_file: "project_report.md"
project_hint: "spring-boot" # Tells the scanner to use Spring-specific heuristics
ignore_patterns:
  - "target/**"       # Maven build output
  - "build/**"        # Gradle build output
  - ".idea/**"
  - ".git/**"

agents:
  coordinator:
    provider: "openai"          # e.g., openai, anthropic, google, local
    model: "gpt-4o"             # Needs high reasoning capabilities for complex jobs
    temperature: 0.2
  
  worker:
    provider: "anthropic"
    model: "claude-3-haiku-20240307" # Cheaper/faster model for simple, bulk reading jobs
    temperature: 0.1
    max_concurrent_workers: 5   # Concurrency limit to prevent rate-limiting
```

## 6. Command Line Interface Design

**Usage:**

```bash
codelens scan [OPTIONS] <PATH>
```

**Examples:**

```bash
codelens scan .  # Scans current directory, uses default config
codelens scan /path/to/repo -c my-config.yaml --hint spring-boot
```

**Flags:**

- `-c, --config`: Path to the configuration YAML file.
- `-o, --output`: Name/Path of the generated markdown file.
- `--hint`: Manually override or set the framework/language hint (e.g., spring-boot, react, django).
- `-v, --verbose`: Print streaming logs of what the Coordinator and Workers are doing.

## 7. Expected Markdown Output Structure

The final generated md file should include the following sections:

- **Project Title & Executive Summary:** A 2-3 paragraph overview of what the project does.
- **Tech Stack & Dependencies:** Major dependencies extracted from pom.xml or build.gradle (e.g., Java 17, Spring Boot 3.2, PostgreSQL, Hibernate).
- **Application Architecture:** A high-level explanation of the folder architecture and module breakdown.
- **Core Components (Spring Specific):**
  - **API Endpoints:** A list of discovered REST controllers and their primary routes.
  - **Business Services:** Summary of the core business logic.
  - **Data Models:** A list of primary database Entities discovered.
- **Getting Started:** Inferred instructions on how to build or run the project (e.g., mvn spring-boot:run or environment variables needed from application.yml).
- **Missing Pieces / Analysis:** Notes from the LLM on any missing documentation, complex areas, or potential tech debt noticed during the scan.

## 8. Edge Cases & Considerations

- **Token Limits:** Even with summaries, a massive project could overwhelm the Coordinator. If Worker summaries exceed the Coordinator's context window, a middle tier of "Sub-Coordinators" (Tree of Thought) must be implemented to aggregate directories before final aggregation.
- **Security:** Ensure the tool does not accidentally upload sensitive environment variables (.env files or secrets within application.yml) to external LLM APIs. The tool must hard-ignore common secret files.
- **Cost Management:** Scanning a massive monorepo with API-based LLMs could get expensive. The CLI should offer a --dry-run or --estimate flag to output the number of tokens that will be processed before executing the API calls.

## 9. Proposed Project Structure (Python Implementation)

Based on the recommendation to use Python frameworks (CrewAI, LangGraph, AutoGen), the following directory structure is proposed for the CLI tool:

```
codelens-cli/
├── codelens/                       # Main application package
│   ├── __init__.py
│   ├── cli.py                      # Command Line Interface entry point (e.g., using Click or Typer)
│   ├── config/
│   │   ├── __init__.py
│   │   └── parser.py               # Logic to load and parse `codelens.config.yaml`
│   ├── core/
│   │   ├── __init__.py
│   │   ├── discovery.py            # Phase 1 & 2: Root scanning, heuristics, and README ingestion
│   │   └── chunking.py             # Logic for chunking files and ignoring patterns
│   ├── agents/                     # The Multi-Agent System
│   │   ├── __init__.py
│   │   ├── coordinator_agent.py    # Manages the overall process and final markdown aggregation
│   │   └── worker_agent.py         # Handles deep dives into specific chunks of source code
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── coordinator.txt         # System prompts for the expensive model
│   │   ├── worker_java_spring.txt  # Spring-specific extraction prompts for the cheap model
│   │   └── worker_generic.txt
│   └── output/
│       ├── __init__.py
│       └── markdown_builder.py     # Constructs the final report based on Section 7
├── tests/                          # Unit and integration tests
│   ├── test_discovery.py
│   └── test_agents.py
├── venv/                           # Virtual environment (git-ignored)
├── .gitignore                      # Git ignore file (includes venv/, .env, __pycache__, etc.)
├── codelens.config.yaml            # Example configuration file
├── requirements.txt                # Python dependencies (e.g., crewai, pyyaml, click)
├── setup.py                        # Installation script so users can run `codelens scan` globally
├── Makefile                        # Development and build automation
├── .env.example                    # Example environment variables
└── README.md                       # Documentation
```

## 10. Makefile for Development

A Makefile will streamline common development tasks:

```makefile
.PHONY: install dev test clean run lint format help venv

# Default target
help:
	@echo "CodeLens CLI - Available Commands:"
	@echo "  make venv       - Create a virtual environment"
	@echo "  make install    - Install the package in production mode"
	@echo "  make dev        - Install the package in development mode with dev dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linting checks (flake8, pylint)"
	@echo "  make format     - Format code with black and isort"
	@echo "  make run        - Run the CLI tool on current directory"
	@echo "  make clean      - Remove build artifacts and cache files"
	@echo "  make build      - Build distribution packages"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source venv/bin/activate  (macOS/Linux)"
	@echo "  venv\\Scripts\\activate     (Windows)"

# Install production dependencies
install:
	@echo "Installing CodeLens CLI..."
	@test -d venv || (echo "WARNING: Virtual environment not found. Run 'make venv' first.")
	pip install -e .

# Install development dependencies
dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	pip install black flake8 pylint pytest pytest-cov isort

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=codelens --cov-report=html --cov-report=term

# Lint code
lint:
	@echo "Running linters..."
	flake8 codelens/ --max-line-length=120
	pylint codelens/ --max-line-length=120

# Format code
format:
	@echo "Formatting code..."
	black codelens/ tests/ --line-length=120
	isort codelens/ tests/ --profile black

# Run the CLI tool
run:
	@echo "Running CodeLens scan on current directory..."
	codelens scan . --verbose

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf venv/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	python setup.py sdist bdist_wheel

# Check if API keys are set
check-env:
	@echo "Checking environment variables..."
	@test -n "$$OPENAI_API_KEY" || (echo "ERROR: OPENAI_API_KEY not set" && exit 1)
	@test -n "$$ANTHROPIC_API_KEY" || (echo "WARNING: ANTHROPIC_API_KEY not set")
	@echo "Environment variables OK"
```

## 11. Installation & Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager
- API keys for OpenAI and/or Anthropic

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/codelens-cli.git
   cd codelens-cli
   ```

2. **Create and activate virtual environment:**
   ```bash
   make venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate     # On Windows
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Install the tool:**
   ```bash
   make install
   # OR for development
   make dev
   ```

5. **Verify installation:**
   ```bash
   codelens --version
   make check-env
   ```

6. **Run your first scan:**
   ```bash
   codelens scan /path/to/spring-boot-project --hint spring-boot
   ```

### Development Workflow

```bash
# Activate virtual environment (always do this first)
source venv/bin/activate

# Install dev dependencies
make dev

# Format code before committing
make format

# Run linters
make lint

# Run tests
make test

# Build distribution
make build

# Deactivate when done
deactivate
```umentation for your own CLI tool
