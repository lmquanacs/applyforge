# Career AI

An automated career coach in your terminal. Review CVs, polish them for maximum impact, generate tailored cover letters, score ATS keyword matches, prep for interviews, and run a full auto-apply pipeline — all grounded strictly in your CV with zero hallucination.

## What's new in v2.0

- **URL scraping** — pass a job posting URL directly instead of copying text
- **Interview prep** — STAR-method prep guide tailored to a specific JD
- **ATS scoring** — local keyword match score, zero API cost
- **Chat coach** — interactive terminal session with persistent memory
- **Natural language mode** — `career-ai ask "..."` routes plain English to the right command
- **Career Vault** — local RAG from your LinkedIn export, brag doc, and performance reviews
- **Auto-Apply pipeline** — one command runs ATS score → CV generation → cover letter → interview prep via LangGraph
- **Data hygiene** — `clean` and `reset` commands to manage local data

All v1.0 commands work exactly as before.

---

## Installation

```bash
git clone https://github.com/your-org/career-ai.git
cd career-ai
make setup
source venv/bin/activate
```

---

## Quick start

```bash
career-ai init                                          # write default config
career-ai cv review ./my_cv.pdf                         # structured feedback
career-ai cv polish ./my_cv.pdf --pdf                   # rewrite + export PDF
career-ai coverletter write ./my_cv.pdf --jd ./jd.txt   # cover letter from file
career-ai coverletter write ./my_cv.pdf --url "https://jobs.example.com/123"  # from URL
career-ai cv ats-score ./my_cv.pdf --url "https://jobs.example.com/123"       # ATS score
career-ai interview prep ./my_cv.pdf --url "https://jobs.example.com/123"     # prep guide
career-ai agent apply ./my_cv.pdf --url "https://..." --company Stripe --role "Backend Engineer"
```

---

## Configuration

```bash
career-ai init                                    # creates ~/.config/career-ai/config.yaml
career-ai config set model.default gpt-4o
career-ai config set model.fallback claude-3-5-sonnet-20241022
career-ai config set tokens.max_input_limit 16000
career-ai config set app.max_cover_letter_words 150
```

Add API keys to `.env`:

```bash
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
GEMINI_API_KEY=<your_gemini_api_key>
# OLLAMA_API_BASE=http://localhost:11434
```

Supported providers: OpenAI, Anthropic, Google Gemini, Ollama (local). Any model string supported by [LiteLLM](https://github.com/BerriAI/litellm) works.

---

## Commands at a glance

| Command | Description |
|---|---|
| `career-ai cv review <file>` | Structured feedback report |
| `career-ai cv polish <file>` | Rewrite CV with action verbs + STAR |
| `career-ai cv ats-score <file>` | Local keyword match score vs JD |
| `career-ai cv generate <file>` | RAG-powered tailored CV from Vault |
| `career-ai coverletter write <file>` | Tailored cover letter |
| `career-ai interview prep <file>` | STAR-method interview prep guide |
| `career-ai chat` | Interactive coaching session with memory |
| `career-ai ask "<prompt>"` | Natural language → command routing |
| `career-ai vault ingest <file>` | Add document to Career Vault |
| `career-ai vault clear` | Remove all vault data |
| `career-ai agent apply <file>` | Full auto-apply pipeline (LangGraph) |
| `career-ai clean` | Remove generated output files |
| `career-ai clean --history` | Clear chat session memory |
| `career-ai reset --hard` | Factory reset (DB + vault + config) |

Add `--dry-run` / `-d` to any LLM command to preview tokens and cost without making an API call.

---

## Project structure

```
career-ai/
├── career_ai/
│   ├── cli.py
│   ├── config.py
│   ├── default_config.yaml
│   ├── core/
│   │   ├── extractor.py        # PDF / DOCX / MD / TXT parsing
│   │   ├── reviewer.py         # CV review prompts
│   │   ├── polisher.py         # CV polish prompts
│   │   ├── generator.py        # Cover letter prompts
│   │   ├── interviewer.py      # Interview prep prompts
│   │   ├── ats.py              # Local ATS keyword scoring
│   │   └── scraper.py          # URL → JD text extraction
│   ├── llm/
│   │   ├── client.py           # LiteLLM wrapper, dry-run, fallback
│   │   └── tokens.py           # Token counting and cost estimation
│   ├── agent/
│   │   ├── state.py            # AgentState TypedDict
│   │   ├── nodes.py            # LangGraph node functions
│   │   └── graph.py            # Graph definition and compilation
│   ├── vault/
│   │   ├── ingest.py           # Chunk, embed, store documents
│   │   └── query.py            # Retrieve relevant chunks
│   └── utils/
│       ├── logging.py          # SQLite usage log + chat history
│       └── output.py           # Save .md or .pdf output
└── tests/
```

---

## Developer commands

```bash
make setup    # create venv, install deps, copy .env.example → .env
make test     # run pytest
make lint     # black, flake8, mypy
make clean    # remove __pycache__, build artifacts
```

For full usage details, flags, and examples see [docs/user-guide.md](docs/user-guide.md).
