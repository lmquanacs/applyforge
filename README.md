# Career AI

A command-line tool that acts as an automated career coach. It reviews CVs, polishes them for maximum impact, and generates tailored cover letters — all grounded strictly in your CV with zero hallucination.

## Features

- **CV Review** — structured feedback with score, strengths, gaps, and rewrite suggestions
- **CV Polish** — rewrites your CV using strong action verbs and STAR format, no invented facts
- **Cover Letter** — cross-references your CV against a JD to produce a factually accurate letter
- **Bring Your Own Model** — works with OpenAI, Anthropic, Google Gemini, or a local Ollama model
- **Dry Run** — preview token count and cost before making any API call
- **Usage Logging** — every request is logged to a local SQLite DB for cost auditing

---

## Installation

```bash
git clone https://github.com/your-org/career-ai.git
cd career-ai
make setup
```

This creates a `venv/`, installs all dependencies, and copies `.env.example` → `.env`.

Then activate the environment:

```bash
source venv/bin/activate
```

---

## Configuration

### Step 1 — Add your API key(s)

Edit `.env` in the project root and add the key for your chosen provider:

```bash
# OpenAI
OPENAI_API_KEY=<your_openai_api_key>

# Anthropic
ANTHROPIC_API_KEY=<your_anthropic_api_key>

# Google Gemini
GEMINI_API_KEY=<your_gemini_api_key>

# Ollama (local) — no key needed, just set the base URL if non-default
# OLLAMA_API_BASE=http://localhost:11434
```

### Step 2 — Initialise the config file

```bash
career-ai init
```

This writes the default config to `~/.config/career-ai/config.yaml`:

```yaml
model:
  default: "gpt-4o"
  fallback: "claude-3-5-sonnet-20241022"
  temperature: 0.1

tokens:
  max_input_limit: 16000
  max_output_limit: 2000
  warn_cost_threshold: 0.10

app:
  log_usage: true
  usage_db_path: "~/.config/career-ai/usage.db"
```

### Step 3 — Set your preferred model

Use `career-ai config set <key> <value>` to update any config field:

```bash
career-ai config set model.default gpt-4o
career-ai config set model.fallback gpt-4o-mini
```

---

## Bring Your Own Model

Career AI uses [LiteLLM](https://github.com/BerriAI/litellm) as the routing layer, so any provider LiteLLM supports works out of the box.

### OpenAI

```bash
# .env
OPENAI_API_KEY=<your_openai_api_key>

career-ai config set model.default gpt-4o
career-ai config set model.fallback gpt-4o-mini
```

Supported model names: `gpt-4.1`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`

---

### Anthropic (Claude)

```bash
# .env
ANTHROPIC_API_KEY=<your_anthropic_api_key>

career-ai config set model.default claude-3-5-sonnet-20241022
career-ai config set model.fallback claude-3-haiku-20240307
```

Supported model names: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`

---

### Google Gemini

```bash
# .env
GEMINI_API_KEY=<your_gemini_api_key>

career-ai config set model.default gemini/gemini-1.5-pro
career-ai config set model.fallback gemini/gemini-1.5-flash
```

Supported model names: `gemini/gemini-1.5-pro`, `gemini/gemini-1.5-flash`

---

### Local Model via Ollama

No API key required. Make sure [Ollama](https://ollama.com) is running locally.

```bash
# Pull a model first
ollama pull llama3

career-ai config set model.default ollama/llama3
career-ai config set model.fallback ollama/llama3
```

Supported model names: `ollama/llama3`, `ollama/mistral`, `ollama/codellama`, or any model you have pulled.

> By default Ollama runs at `http://localhost:11434`. If you changed the port, set `OLLAMA_API_BASE=http://localhost:<port>` in `.env`.

---

### Per-command model override

You can override the configured model for any single command using `--model`:

```bash
career-ai review ./my_cv.pdf --model gpt-4o-mini
career-ai write ./my_cv.pdf --jd ./jd.txt --model claude-3-5-sonnet-20241022
career-ai polish ./my_cv.pdf --model ollama/llama3
```

---

## Usage

### Review a CV

```bash
career-ai review ./my_cv.pdf
```

Outputs a structured Markdown report with score, strengths, gaps, and rewrite suggestions.

```bash
# Supported input formats: .pdf, .docx, .md, .txt
career-ai review ./my_cv.docx
career-ai review ./my_cv.md
```

---

### Polish a CV

```bash
career-ai polish ./my_cv.pdf --out output/polished_cv.md
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--out` | `output/polished_cv.md` | Output file (`.md` or `.pdf`) |
| `--pdf` | `false` | Also export a styled PDF to `output/polished_cv.pdf` |
| `--tone` | `professional` | `executive`, `technical`, `sales` |
| `--focus` | `general` | e.g. `leadership`, `backend engineering` |

```bash
# Polish and export both .md and .pdf
career-ai polish ./my_cv.pdf --pdf

career-ai polish ./my_cv.pdf --tone executive --focus leadership --out output/polished_cv.md --pdf
```

---

### Generate a Cover Letter

```bash
career-ai write ./my_cv.pdf --jd ./jd.txt --out output/cover_letter.md
```

The `--jd` flag accepts a file path or a raw string:

```bash
# From a file
career-ai write ./my_cv.pdf --jd ./jd.txt

# As a raw string
career-ai write ./my_cv.pdf --jd "We need a Python developer with 5 years experience..."
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--jd` | *(required)* | Path to JD file or raw JD text |
| `--out` | `output/cover_letter.md` | Output file (`.md` or `.pdf`) |
| `--tone` | `professional` | `formal`, `startup/casual`, `confident` |

> The cover letter body is capped at `app.max_cover_letter_words` (default: 120 words). Override with `career-ai config set app.max_cover_letter_words 200`.

---

### Dry Run (preview before spending)

Add `--dry-run` or `-d` to any command to see the token count, estimated cost, and full prompt — without making an API call:

```bash
career-ai review ./my_cv.pdf --dry-run
career-ai write ./my_cv.pdf --jd ./jd.txt --dry-run
career-ai polish ./my_cv.pdf --dry-run
```

---

## Cost & Token Management

The config controls guardrails applied before every API call:

```yaml
tokens:
  max_input_limit: 16000    # Aborts if input exceeds this token count
  max_output_limit: 4000    # Hard cap on generated output length
  warn_cost_threshold: 0.10 # Prints a warning if estimated cost exceeds $0.10

app:
  log_usage: true
  usage_db_path: "~/.config/career-ai/usage.db"
  max_cover_letter_words: 120  # Hard cap on cover letter body length
```

Update via CLI:

```bash
career-ai config set tokens.max_input_limit 8000
career-ai config set tokens.max_output_limit 4000
career-ai config set tokens.warn_cost_threshold 0.05
career-ai config set app.max_cover_letter_words 200
```

All successful requests are logged to `~/.config/career-ai/usage.db` (SQLite) with timestamp, model, token counts, and cost.

---

## Output Files

All generated files are saved to the `output/` folder by default. Both `.md` and `.pdf` are supported:

```bash
career-ai write ./my_cv.pdf --jd ./jd.txt --out output/cover_letter.pdf
career-ai polish ./my_cv.pdf --out output/polished_cv.md --pdf
```

---

## Developer Commands

```bash
make setup    # Create venv, install dependencies, copy .env.example → .env
make test     # Run test suite with pytest
make lint     # Run black, flake8, mypy
make clean    # Remove __pycache__, .pytest_cache, build artifacts
```

---

## Project Structure

```
career-ai/
├── .env                        # API keys (git ignored)
├── .env.example                # Key template for new developers
├── Makefile
├── requirements.txt
├── pyproject.toml
├── career_ai/
│   ├── cli.py                  # Entry point — all CLI commands
│   ├── config.py               # Config loading and validation
│   ├── default_config.yaml     # Shipped defaults
│   ├── core/
│   │   ├── extractor.py        # PDF / DOCX / MD / TXT parsing
│   │   ├── reviewer.py         # CV review prompts
│   │   ├── polisher.py         # CV polish prompts
│   │   └── generator.py        # Cover letter prompts
│   ├── llm/
│   │   ├── client.py           # LiteLLM wrapper, dry-run, fallback
│   │   └── tokens.py           # Token counting and cost estimation
│   └── utils/
│       ├── logging.py          # SQLite usage log + rich console
│       └── output.py           # Save .md or .pdf output
└── tests/
    ├── test_cli.py
    └── test_extractor.py
```
