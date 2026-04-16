# Career AI — User Guide

## Table of contents

1. [Installation](#1-installation)
2. [Configuration](#2-configuration)
3. [Bring your own model](#3-bring-your-own-model)
4. [CV file resolution](#4-cv-file-resolution)
5. [CV commands](#5-cv-commands)
6. [Cover letter](#6-cover-letter)
7. [Interview prep](#7-interview-prep)
8. [ATS scoring](#8-ats-scoring)
9. [Chat coach](#9-chat-coach)
10. [Natural language mode](#10-natural-language-mode)
11. [Career Vault (RAG)](#11-career-vault-rag)
12. [Auto-Apply pipeline](#12-auto-apply-pipeline)
13. [Data management](#13-data-management)
14. [Cost and token management](#14-cost-and-token-management)
15. [Output files](#15-output-files)

---

## 1. Installation

```bash
git clone https://github.com/your-org/career-ai.git
cd career-ai
make setup
source venv/bin/activate
```

`make setup` creates a `venv/`, installs all dependencies, installs the `career-ai` command, and copies `.env.example` → `.env`.

---

## 2. Configuration

### Initialise

```bash
career-ai init
```

Writes the default config to `~/.config/career-ai/config.yaml`:

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
  max_cover_letter_words: 120
  chat_session_id: "default"
  vault_top_k: 8
  working_dir: "~/Documents/career-ai"   # default directory for CV files
  default_cv_path: ""                     # pin a specific CV file
```

### Update any value

```bash
career-ai config set model.default gpt-4o
career-ai config set model.fallback claude-3-5-sonnet-20241022
career-ai config set tokens.max_input_limit 16000
career-ai config set tokens.max_output_limit 4000
career-ai config set tokens.warn_cost_threshold 0.05
career-ai config set app.max_cover_letter_words 200
career-ai config set app.vault_top_k 10
career-ai config set app.working_dir ~/Documents/career-ai
career-ai config set app.default_cv_path ~/Documents/career-ai/my_cv.pdf
```

### API keys

Edit `.env` in the project root:

```bash
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
GEMINI_API_KEY=<your_gemini_api_key>
# OLLAMA_API_BASE=http://localhost:11434
```

---

## 3. Bring your own model

Career AI uses [LiteLLM](https://github.com/BerriAI/litellm) as the routing layer. Any provider LiteLLM supports works out of the box.

### OpenAI

```bash
career-ai config set model.default gpt-4o
career-ai config set model.fallback gpt-4o-mini
```

Model names: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Anthropic

```bash
career-ai config set model.default claude-3-5-sonnet-20241022
career-ai config set model.fallback claude-3-haiku-20240307
```

Model names: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`

### Google Gemini

```bash
career-ai config set model.default gemini/gemini-1.5-pro
career-ai config set model.fallback gemini/gemini-1.5-flash
```

### Ollama (local, no API key)

```bash
ollama pull llama3
career-ai config set model.default ollama/llama3
career-ai config set model.fallback ollama/llama3
```

> If Ollama runs on a non-default port, set `OLLAMA_API_BASE=http://localhost:<port>` in `.env`.

### Per-command override

```bash
career-ai cv review ./my_cv.pdf --model gpt-4o-mini
career-ai coverletter write ./my_cv.pdf --jd ./jd.txt --model claude-3-5-sonnet-20241022
```

---

## 4. CV file resolution

Every command that takes a CV file accepts it as an optional positional argument. If you omit it, the tool resolves it automatically using this priority order:

| Priority | Source | How it works |
|---|---|---|
| 1 | Explicit argument | `career-ai cv review ./my_cv.pdf` — always wins |
| 2 | `app.default_cv_path` | A specific file you pinned in config |
| 3 | Auto-discover | If `app.working_dir` contains exactly one `.pdf` or `.docx`, it is used automatically |

If none of the three resolve, the command exits with a clear error and instructions.

### Set a default CV

```bash
# Option A — pin a specific file
career-ai config set app.default_cv_path ~/Documents/career-ai/my_cv.pdf

# Option B — set a working directory and drop your CV there
# (auto-discovered only if it is the single PDF/DOCX in that folder)
career-ai config set app.working_dir ~/Documents/career-ai
```

Once set, all of these work without typing the file path:

```bash
career-ai cv review
career-ai cv polish --pdf
career-ai cv ats-score --url "https://jobs.example.com/123"
career-ai coverletter write --url "https://jobs.example.com/123"
career-ai interview prep --url "https://jobs.example.com/123"
career-ai agent apply --url "https://..." --company Stripe --role "Backend Engineer"
```

The `ask` command also benefits — the router is told your default CV path, so `career-ai ask "Score my CV against the job at https://jobs.example.com/123"` resolves correctly without you specifying a file name.

---

## 5. CV commands

### Review

Produces a structured Markdown report: overall score, strengths, weaknesses, and actionable rewrites.

```bash
career-ai cv review                  # uses default CV
career-ai cv review ./my_cv.pdf      # explicit path
career-ai cv review ./my_cv.docx
```

Supported input formats: `.pdf`, `.docx`, `.md`, `.txt`

| Flag | Default | Description |
|---|---|---|
| `--model` | config default | Override LLM |
| `--dry-run` / `-d` | false | Preview tokens + cost, no API call |

### Polish

Rewrites the CV using strong action verbs and STAR format. No new facts are invented.

```bash
career-ai cv polish                                          # uses default CV
career-ai cv polish ./my_cv.pdf --out output/polished_cv.md --pdf
career-ai cv polish ./my_cv.pdf --tone executive --focus leadership
```

| Flag | Default | Description |
|---|---|---|
| `--out` | `output/polished_cv.md` | Output path (`.md` or `.pdf`) |
| `--pdf` | false | Also export a styled PDF |
| `--tone` | `professional` | `executive`, `technical`, `sales` |
| `--focus` | `general` | e.g. `leadership`, `backend engineering` |
| `--model` | config default | Override LLM |
| `--dry-run` / `-d` | false | Preview without API call |

### ATS score

Scores how well your CV matches a JD using local keyword analysis. No API call, no cost.

```bash
career-ai cv ats-score --url "https://jobs.example.com/123"        # uses default CV
career-ai cv ats-score ./my_cv.pdf --jd ./jd.txt
career-ai cv ats-score ./my_cv.pdf --url "https://jobs.example.com/123"
```

Output example:

```
ATS Match Score: 74%
Matched keywords (31): python, api, backend, django, postgresql, ...
Missing keywords (11):
  • kubernetes
  • terraform
  • grpc
```

| Flag | Description |
|---|---|
| `--jd` | Path to JD file or raw JD text |
| `--url` | URL of the job posting (scrapes automatically) |

### Generate (RAG-powered)

Generates a fully tailored CV by querying the Career Vault for your most relevant achievements, then rewriting against the JD. Requires vault setup — see [Career Vault](#11-career-vault-rag).

```bash
career-ai cv generate --url "https://jobs.example.com/123"                        # uses default CV
career-ai cv generate ./my_cv.pdf --jd ./jd.txt --out output/tailored_cv.md --pdf
```

| Flag | Default | Description |
|---|---|---|
| `--jd` | — | Path to JD file or raw JD text |
| `--url` | — | URL of the job posting |
| `--out` | `output/generated_cv.md` | Output path |
| `--pdf` | false | Also export a styled PDF |
| `--model` | config default | Override LLM |
| `--dry-run` / `-d` | false | Preview without API call |

---

## 6. Cover letter

Generates a tailored cover letter by cross-referencing your CV against the JD. Only facts present in your CV are used.

```bash
# Uses default CV
career-ai coverletter write --url "https://jobs.example.com/123"

# Explicit CV path
career-ai coverletter write ./my_cv.pdf --jd ./jd.txt

# Raw JD string
career-ai coverletter write ./my_cv.pdf --jd "We need a Python developer with 5 years experience..."

# With tone and PDF output
career-ai coverletter write --url "https://jobs.example.com/123" \
  --tone confident --out output/cover_letter.pdf
```

| Flag | Default | Description |
|---|---|---|
| `--jd` | — | Path to JD file or raw JD text |
| `--url` | — | URL of the job posting |
| `--out` | `output/cover_letter.md` | Output path (`.md` or `.pdf`) |
| `--tone` | `professional` | `formal`, `startup/casual`, `confident` |
| `--model` | config default | Override LLM |
| `--dry-run` / `-d` | false | Preview without API call |

> The cover letter body is capped at `app.max_cover_letter_words` (default: 120). Increase with `career-ai config set app.max_cover_letter_words 200`.

---

## 7. Interview prep

Generates a STAR-method interview prep guide mapped to the specific JD. Only real CV achievements are used.

```bash
career-ai interview prep --url "https://jobs.example.com/123"                    # uses default CV
career-ai interview prep ./my_cv.pdf --jd ./jd.txt --out output/interview_prep.md
```

Output includes:
- Likely behavioural questions with STAR answers drawn from your CV
- Likely technical topics based on JD requirements you already meet
- Key talking points — your strongest relevant achievements

| Flag | Default | Description |
|---|---|---|
| `--jd` | — | Path to JD file or raw JD text |
| `--url` | — | URL of the job posting |
| `--out` | `output/interview_prep.md` | Output path |
| `--model` | config default | Override LLM |
| `--dry-run` / `-d` | false | Preview without API call |

---

## 8. ATS scoring

See [CV → ATS score](#ats-score) above. The scorer runs entirely locally using tokenisation and set intersection — no embeddings, no API calls, instant results.

The score reflects keyword overlap between your CV and the JD. Use it before polishing or generating a CV to understand the gap.

---

## 9. Chat coach

An interactive terminal session with a career coach that remembers your conversation across sessions.

```bash
career-ai chat
career-ai chat --session job-search-2025   # named session
career-ai chat --model claude-3-5-sonnet-20241022
```

- Type naturally — ask about your CV, a specific role, salary negotiation, anything career-related
- The coach has full context of the current session
- Sessions are saved to `~/.config/career-ai/usage.db` and resume automatically when you use the same `--session` name
- Type `exit` or press `Ctrl+C` to end the session

| Flag | Default | Description |
|---|---|---|
| `--session` / `-s` | `default` | Session name to create or resume |
| `--model` | config default | Override LLM |

To clear all chat history:

```bash
career-ai clean --history
```

---

## 10. Natural language mode

Translates a plain English instruction into the appropriate `career-ai` command and runs it.

```bash
career-ai ask "Review my CV"
career-ai ask "Write a confident cover letter for the job at https://jobs.example.com/123"
career-ai ask "Score my CV against the job at https://jobs.example.com/123"
career-ai ask "Prep me for the interview at Stripe for https://jobs.stripe.com/456"
```

A fast, low-cost model (`gpt-4o-mini` by default) acts as a router — it parses your intent, maps it to the correct command and flags, then executes it.

If `app.default_cv_path` or `app.working_dir` is configured, the router is automatically told your CV path so you never need to mention the filename in natural language prompts.

| Flag | Default | Description |
|---|---|---|
| `--model` | `gpt-4o-mini` | Override the router model |

---

## 11. Career Vault (RAG)

The Career Vault is a local vector database that stores your full career history — LinkedIn exports, performance reviews, brag documents, old CVs. When generating a tailored CV, the tool queries the vault for the most relevant achievements rather than being limited to what fits on two pages.

### Ingest documents

```bash
career-ai vault ingest ./linkedin_export.pdf
career-ai vault ingest ./performance_review_2024.docx
career-ai vault ingest ./brag_document.md
```

Supported formats: `.pdf`, `.docx`, `.md`, `.txt`

Each document is chunked, embedded locally using `sentence-transformers/all-MiniLM-L6-v2` (no API cost), and stored in a local ChromaDB database at `~/.config/career-ai/vault/`.

### Generate a tailored CV using the vault

```bash
career-ai cv generate --url "https://jobs.example.com/123"          # uses default CV
career-ai cv generate ./my_cv.pdf --url "https://jobs.example.com/123"
```

The tool embeds the JD, retrieves the top-k most relevant chunks from your vault, and uses them as additional context when rewriting your CV.

Adjust how many chunks are retrieved:

```bash
career-ai config set app.vault_top_k 10
```

### Clear the vault

```bash
career-ai vault clear
```

Drops all documents from the local vector store. Your source files are not affected.

---

## 12. Auto-Apply pipeline

Runs the full job application workflow in a single command, powered by a [LangGraph](https://github.com/langchain-ai/langgraph) stateful pipeline.

```bash
# Uses default CV
career-ai agent apply \
  --url "https://jobs.example.com/123" \
  --company "Stripe" \
  --role "Backend Engineer"

# Explicit CV path
career-ai agent apply ./my_cv.pdf \
  --url "https://jobs.example.com/123" \
  --company "Stripe" \
  --role "Backend Engineer"
```

### What it does

```
extract_jd → ats_score → vault_query → generate_cv → generate_cover_letter → generate_interview_prep → summarise
```

1. Scrapes the JD from the URL
2. Scores ATS keyword match and prints missing keywords
3. Queries the Career Vault for relevant achievements
4. Generates a tailored CV
5. Generates a cover letter
6. Generates an interview prep guide
7. Prints a summary of the full package

### Output

All files are saved to `output/<Company>_<Role>/`:

```
output/Stripe_Backend_Engineer/
├── cv.md
├── cover_letter.md
└── interview_prep.md
```

### Failure recovery

If JD extraction fails, the graph automatically retries with a fallback scraper before continuing. The pipeline state is checkpointed to `~/.config/career-ai/usage.db` after each step — if a run is interrupted, re-running the same command resumes from the last completed node.

| Flag | Description |
|---|---|
| `--url` | URL of the job posting (required) |
| `--company` | Company name, used for the output folder (required) |
| `--role` | Role title, used for the output folder (required) |

---

## 13. Data management

### Remove generated output files

```bash
career-ai clean
```

Deletes all `.md` and `.pdf` files from the `output/` directory.

### Clear chat history

```bash
career-ai clean --history
```

Deletes all chat session messages from the SQLite database. Usage logs are not affected.

### Factory reset

```bash
career-ai reset --hard
```

Prompts for confirmation, then:
- Drops the SQLite database (`usage.db`)
- Deletes the Career Vault (`~/.config/career-ai/vault/`)
- Resets `config.yaml` to defaults

---

## 14. Cost and token management

Every LLM command runs a pre-flight check before making an API call:

- If input tokens exceed `tokens.max_input_limit`, the command aborts with an error
- If estimated cost exceeds `tokens.warn_cost_threshold`, a warning is printed
- All successful requests are logged to `~/.config/career-ai/usage.db`

### Dry run

Add `--dry-run` or `-d` to any LLM command to see the token count, estimated cost, and full prompt payload without spending anything:

```bash
career-ai cv review ./my_cv.pdf --dry-run
career-ai coverletter write ./my_cv.pdf --url "https://jobs.example.com/123" --dry-run
career-ai cv polish ./my_cv.pdf --dry-run
career-ai interview prep ./my_cv.pdf --jd ./jd.txt --dry-run
```

### Adjust limits

```bash
career-ai config set tokens.max_input_limit 8000
career-ai config set tokens.max_output_limit 4000
career-ai config set tokens.warn_cost_threshold 0.05
```

### ATS scoring is always free

`career-ai cv ats-score` runs entirely locally — no tokenisation against an API, no cost.

---

## 15. Output files

All generated files default to the `output/` directory. Both `.md` and `.pdf` are supported wherever `--out` is available.

```bash
# Markdown (default)
career-ai cv polish ./my_cv.pdf --out output/polished_cv.md

# PDF directly
career-ai coverletter write ./my_cv.pdf --jd ./jd.txt --out output/cover_letter.pdf

# Both .md and .pdf
career-ai cv polish ./my_cv.pdf --out output/polished_cv.md --pdf
```

Auto-Apply outputs go to `output/<Company>_<Role>/` automatically.
