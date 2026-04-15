# Product & Technical Specification: Career AI Assistant CLI

## 1. Product Overview

- **Name:** Career-AI (CLI)
- **Purpose:** A command-line tool designed to act as an automated career coach and writer. It provides actionable feedback on resumes (CVs), polishes existing CVs for maximum impact, and generates highly tailored, factually accurate cover letters based on specific Job Descriptions (JDs).
- **Core Tenets:** Accuracy (Zero-Hallucination), Extensibility (Multi-model support), and Cost Control (Token management).

---

## 2. Feature Specifications

### 2.1. CV Feedback Engine

**Description:** Analyzes a user's CV to provide structural, grammatical, and impact-oriented feedback.

**Inputs:**
- `cv_file` *(Required)*: Path to the CV. Supported formats: `.pdf`, `.docx`, `.md`, `.txt`.

**Processing:**
- Extracts text while preserving logical sections (Experience, Education, Skills).
- Evaluates against standard Applicant Tracking System (ATS) readability best practices.
- Checks for impact-driven phrasing (e.g., STAR method: Situation, Task, Action, Result).

**Outputs:** A structured Markdown report including:
- **Overall Score:** Out of 100.
- **Strengths:** What the CV does well.
- **Weaknesses/Gaps:** Missing sections or vague bullet points.
- **Actionable Revisions:** Specific suggestions for rewriting weak bullet points.

---

### 2.2. CV Polisher (Enhancement & Rewriting)

**Description:** Rewrites and enhances a user's existing CV to make it sound more professional, impactful, and ATS-friendly without hallucinating new facts.

**Inputs:**
- `cv_file` *(Required)*: Path to the original CV.
- `tone` *(Optional)*: Target tone (e.g., `"executive"`, `"technical"`, `"sales"`). Default: `"professional"`.
- `focus` *(Optional)*: Specific areas to highlight (e.g., `"leadership"`, `"backend engineering"`).

**Processing:**
- Extracts existing bullet points and professional summaries.
- Rephrases weak or passive statements using strong action verbs.
- Restructures existing facts into the STAR format where possible.
- Consolidates multiple skills-related sections (e.g. "Skills", "Technical Skills") into a single `## Technical Skills` section, grouped by category.
- Enforces the Zero-Hallucination architecture to ensure no new skills or metrics are invented during the rewrite.

**Outputs:** A rendered `.md` file (with optional `--pdf` export) containing the polished, ready-to-use CV.

---

### 2.3. Cover Letter Generator

**Description:** Cross-references a candidate's CV with a specific Job Description to draft a highly customized cover letter.

**Inputs:**
- `cv_file` *(Required)*: Path to the CV.
- `jd_input` *(Required)*: Path to a text file, a raw string, or a URL containing the Job Description.
- `tone` *(Optional)*: e.g., `"formal"`, `"startup/casual"`, `"confident"`. Default: `"professional"`.

**Processing:**
- Extracts core requirements from the JD (required skills, years of experience, core responsibilities).
- Maps JD requirements strictly to existing experiences in the CV.
- Formats the output according to standard business letter conventions.

**Outputs:** A rendered `.md` or `.pdf` file containing the finalized cover letter.

---

## 3. Technical & System Requirements

### 3.1. Zero-Hallucination Architecture

**Requirement:** The AI must never invent degrees, job titles, companies, metrics, or skills that are not explicitly present in the provided CV.

**Implementation Strategy:**
- **System Prompting:** Use absolute negative constraints in the system prompt (e.g., *"You are a strict data-mapper. Do not infer or invent any information. If a JD requirement is not met by the CV, you must not mention it."*).
- **Deterministic Generation:** Force the model temperature to `0.0` or `0.1` to eliminate creative variance.
- **Citation Guardrail:** *(Optional but recommended)* Instruct the LLM to internally cite the exact line from the CV that justifies a claim in the cover letter before generating the final text.

---

### 3.2. Model Configuration (via LiteLLM)

**Requirement:** The tool must not be locked into a single AI provider. Users must be able to configure their preferred model.

**Implementation Strategy:**
- Integrate `litellm` as the routing layer.
- Support providers: OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), Google (Gemini 1.5 Pro), and Local Models (Ollama).
- Provide a configuration file (`~/.career-ai/config.yaml`) for setting primary and fallback models, as well as API keys.

---

### 3.3. Token Management & Cost Control

**Requirement:** Prevent accidental massive API bills and provide transparency on token usage.

**Implementation Strategy:**
- **Pre-flight Calculation:** Use standard tokenizers (e.g., `tiktoken`) to count the exact number of tokens in the prompt + CV + JD before sending the request.
- **Hard Limits:** Define `max_input_tokens` in the config. If an extracted CV is 50,000 tokens (e.g., a scanned textbook by mistake), the CLI must abort and warn the user.
- **Usage Tracking:** Log every successful request's token usage (Prompt, Completion, Total) and estimated cost to a local `.sqlite` or `.json` file for user auditing.

---

### 3.4. Dry Run Capability

**Requirement:** Allow users to preview what the tool will do without spending any money or making API calls.

**Implementation Strategy:**
- Introduce a `--dry-run` or `-d` flag to all CLI commands.
- Behavior when activated:
  1. Parse the documents and build the final system/user prompt.
  2. Calculate the estimated token count and cost.
  3. Print the following to the console: Target Model, Total Tokens, Estimated Cost, and the Exact Prompt Payload.
  4. Terminate the process (short-circuit before the LiteLLM API call).

---

## 4. User Interface (CLI Design)

The interface will use a standard POSIX-compliant CLI structure.

**Setup & Config**
```bash
career-ai init
career-ai config set default_model claude-3-5-sonnet-20241022
```

**CV Feedback**
```bash
career-ai review ./my_resume.pdf
career-ai review ./my_resume.pdf --dry-run
```

**CV Polishing**
```bash
career-ai polish ./my_resume.pdf --out output/polished_resume.md
career-ai polish ./my_resume.pdf --tone executive --focus leadership
career-ai polish ./my_resume.pdf --pdf
```

**Cover Letter Generation**
```bash
career-ai write ./my_resume.pdf --jd ./google_swe_jd.txt --out output/cover_letter.pdf
career-ai write ./my_resume.pdf --jd "We need a Python dev with 5 years exp..." --model gpt-4.1
```

---

## 5. Configuration Schema

Stored at `~/.config/career-ai/config.yaml`.

```yaml
# Model Settings
model:
  default: "gpt-4.1"
  fallback: "gpt-4o"
  temperature: 0.1

# Token & Cost Management
tokens:
  max_input_limit: 16000     # Aborts if input exceeds this
  max_output_limit: 4000     # Hard limit on generation length
  warn_cost_threshold: 0.10  # Warns user if estimated cost exceeds $0.10

# Application Settings
app:
  log_usage: true
  usage_db_path: "~/.config/career-ai/usage.db"
```

---

## 6. Error Handling & Edge Cases

- **Unreadable PDFs:** If a PDF is an image (no text layer), the tool must detect the lack of text and gracefully suggest OCR or request a different format.
- **API Rate Limits:** LiteLLM must be configured with retry logic (e.g., exponential backoff) for handling `429 Too Many Requests` errors.
- **Token Overflow:** If the user's CV and JD combined exceed the model's context window, the tool must fail gracefully during the pre-flight check, not after hitting the API.

---

## 7. Recommended Technology Stack & Libraries

### Core CLI & Application Logic
| Library | Purpose |
|---------|---------|
| `typer` | Building the CLI with a modern, type-hinted approach. |
| `pydantic` | Strictly validating the configuration schema and LLM output structures. |
| `pyyaml` | Parsing and managing the `config.yaml` file. |

### LLM Orchestration & Cost Management
| Library | Purpose |
|---------|---------|
| `litellm` | Core routing layer for standardizing API calls across providers. |
| `tiktoken` | Accurate pre-flight token counting and cost estimation. |

### Document Processing (Ingestion)
| Library | Purpose |
|---------|---------|
| `pdfplumber` | Robust text extraction from PDF resumes, handling column layouts. |
| `python-docx` | Parsing text from Word (`.docx`) CVs. |

### Document Generation (Export)
| Library | Purpose |
|---------|---------|
| `markdown` | Standardizing generated text into HTML/Markdown structures. |
| `reportlab` | Rendering polished CVs into professionally styled PDF documents. |
| `jinja2` | *(Optional)* Managing modular system prompts and structural templates. |

### Terminal User Interface (TUI)
| Library | Purpose |
|---------|---------|
| `rich` | Rendering Markdown reviews, progress spinners, and token usage tables. |

---

## 8. Project Structure & Local Development

The project follows a standard Python modular application layout using `venv` for dependency isolation, `.env` for credentials, and a `Makefile` for developer workflows.

### 8.1. Directory Layout

```
career-ai/
├── .env                 # Local environment variables (API keys) - Git ignored
├── .env.example         # Template for required environment variables
├── .gitignore           # Standard Python gitignore (ignores venv/, .env, etc.)
├── Makefile             # Automation commands (setup, install, test, lint)
├── README.md            # Project documentation and setup instructions
├── requirements.txt     # Python dependencies (or pyproject.toml)
├── venv/                # Local Python virtual environment - Git ignored
├── career_ai/           # Main source code directory
│   ├── __init__.py
│   ├── cli.py           # Typer application entry point
│   ├── config.py        # Configuration loading and validation
│   ├── core/            # Core business logic
│   │   ├── __init__.py
│   │   ├── extractor.py # PDF/DOCX parsing logic
│   │   ├── generator.py # Cover letter generation logic
│   │   └── polisher.py  # CV polishing logic
│   ├── llm/             # LLM orchestration and token management
│   │   ├── __init__.py
│   │   ├── client.py    # LiteLLM integration
│   │   └── tokens.py    # Tiktoken counting and cost estimation
│   └── utils/           # Helper functions
│       ├── __init__.py
│       └── logging.py   # Token usage logging and console output
└── tests/               # Unit and integration tests
    ├── __init__.py
    ├── test_cli.py
    └── test_extractor.py
```

### 8.2. Environment Management (.env & venv)

- **`venv`:** All development and execution should occur within an isolated virtual environment to prevent dependency conflicts. The `venv/` folder is excluded from version control.
- **`.env`:** Secrets such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or local model endpoints are stored here. This file is excluded from version control. A `.env.example` is tracked to indicate required keys to new developers. The application uses `python-dotenv` to load these variables at runtime.

### 8.3. Task Automation (Makefile)

| Target | Description |
|--------|-------------|
| `make setup` | Creates the `venv`, upgrades `pip`, installs dependencies, installs the `career-ai` command, and creates `.env` from `.env.example` if absent. |
| `make test` | Runs the test suite using `pytest`. |
| `make lint` | Runs code formatting and linting tools (`black`, `flake8`, `mypy`). |
| `make clean` | Removes `__pycache__`, `.pytest_cache`, built artifacts, and optionally the `venv` directory. |
