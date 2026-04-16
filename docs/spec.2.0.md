# Career AI v2.0 — Product Enhancement Specification

## 1. Executive Summary

This document outlines the roadmap for Career AI v2.0, transitioning the tool from a static document processor to an interactive, agentic career management assistant. The enhancements focus on integrating the latest AI trends: agentic workflows, local Retrieval-Augmented Generation (RAG), web grounding, and conversational UI.

### 1.1 Core Philosophy & Backwards Compatibility

While v2.0 introduces advanced agentic workflows and local RAG, simplicity remains a core tenet. All original v1.0 commands will remain fully supported, fast, and un-bloated.

Users who simply want to process a single document without setting up a Vault or using agents can continue using the standard CLI tools without any friction:

```bash
career-ai cv review ./my_cv.pdf
career-ai cv polish ./my_cv.pdf
career-ai coverletter write ./my_cv.pdf --jd ./jd.txt
```

These base commands will inherit the new under-the-hood improvements (like URL scraping) but will never require the heavier Phase 3 features.

---

## 2. Phase 1 — High-Impact, Low-Effort (Quick Wins)

These features leverage the existing LiteLLM routing and document extraction architecture, requiring minimal new infrastructure.

### 2.1 Live URL Scraping for Job Descriptions

**Problem:** Manually copying and pasting job descriptions into text files is tedious.

**Solution:** Allow users to pass a URL directly to the CLI, bypassing the need for a local `.txt` file.

- New flag: `--url <link>` added to `coverletter write` and upcoming commands
- Implementation: `trafilatura` or `beautifulsoup4` to fetch and parse the main content of a job posting URL, stripping headers, footers, and ads

```bash
career-ai coverletter write ./my_cv.pdf --url "https://jobs.lever.co/example/123"
```

### 2.2 Automated Interview Preparation

**Problem:** The tool stops at the application phase. Users need help converting CV achievements into spoken answers.

**Solution:** A new sub-command that generates a customised interview prep sheet based on the CV and JD intersection.

- New command: `career-ai interview prep`
- Analyses the JD for likely behavioural and technical questions
- Maps the user's CV to the STAR method for those specific questions
- Outputs a styled markdown guide to `output/interview_prep.md`

```bash
career-ai interview prep ./my_cv.pdf --url <jd_url>
```

---

## 3. Phase 2 — Core Architecture Upgrades (Medium Effort)

These features require adding new dependencies (local NLP, interactive CLI libraries) to enhance user experience and transparency.

### 3.1 Local ATS Match & Keyword Analysis

**Problem:** Users want objective metrics on how well their CV matches a JD before spending tokens on an LLM rewrite.

**Solution:** A local, deterministic keyword/semantic matching engine that mimics legacy Applicant Tracking Systems (ATS).

- New command: `career-ai cv ats-score`
- Implementation: `spacy` or TF-IDF via `scikit-learn` to extract hard skills and keywords from the JD, compared against the CV locally (zero API cost)
- Output: match percentage (e.g. `74%`) and a list of missing keywords

### 3.2 Agentic "Coach" Mode (Conversational Agent with Memory)

**Problem:** Users often have iterative, specific questions about their CV and want an assistant that remembers context across sessions and can execute actions autonomously.

**Solution:** An interactive, agentic terminal session that maintains context and uses function-calling to execute tool commands on the user's behalf.

- New command: `career-ai chat`
- Implementation: `prompt_toolkit` + `rich` for a dynamic terminal chat UI
- Memory retention: chat history saved to the local SQLite DB (`usage.db` expanded with a `sessions` table), allowing users to resume previous coaching sessions
- Agentic tool use: enabled via LiteLLM function calling — the LLM can autonomously trigger underlying Python functions (e.g. "Scrape this JD and tell me my ATS score" runs the scraper and ATS scorer, then replies)

### 3.3 Natural Language Intent Parsing ("English Mode")

**Problem:** Remembering CLI syntax, flags, and file paths can be frustrating for non-technical users.

**Solution:** A natural language entry point that translates English instructions into the appropriate tool execution under the hood.

- New command: `career-ai ask "<prompt>"` (or simply `career-ai "<prompt>"`)
- Implementation: a fast, low-cost LLM call (e.g. `gpt-4o-mini` or `haiku`) as a router — parses the user's string, identifies intent, maps it to available CLI commands and arguments, and executes the underlying Python function

```bash
# Instead of:
career-ai coverletter write ./cv.pdf --url https://job.com --tone confident

# Use:
career-ai ask "Write a confident cover letter using my cv.pdf for the job at https://job.com"
```

### 3.4 Data Management & Privacy (Cleanup Commands)

**Problem:** With SQLite logging, chat history memory, and local project folders, users need a simple way to purge their data for privacy, storage, or a fresh start.

**Solution:** Global and scoped `clean` and `reset` commands.

- New commands: `career-ai clean`, `career-ai reset`

| Command | Behaviour |
|---|---|
| `career-ai clean` | Wipes the local `output/` directory of all generated PDFs and MDs |
| `career-ai clean --history` | Deletes chat session memory from the local SQLite database |
| `career-ai reset --hard` | Factory reset — drops the SQLite DB, clears the Vault, resets `config.yaml` to defaults |

```bash
career-ai clean --history    # Clears LLM chat memory
career-ai reset --hard       # Wipes all data and resets config
```

---

## 4. Phase 3 — Advanced Agentic Workflows (High Effort)

These features introduce local vector databases and multi-step agent pipelines, representing the biggest leap in functionality.

### 4.1 "Career Vault" (Local RAG)

**Problem:** A single CV is often truncated. Tailoring a CV requires the AI to know the user's entire career history, not just what fits on two pages.

**Solution:** A local vector database containing the user's master career data.

- New commands: `career-ai vault ingest`, `career-ai vault clear`, `career-ai cv generate`
- Implementation: `chromadb` or `lancedb` (local, lightweight vector stores) + `sentence-transformers` for local embeddings (zero token cost during ingest)
- Users ingest their LinkedIn export, performance reviews, and a "brag document"
- `career-ai cv generate --url <jd_url>` queries the Vault for the most relevant achievements and builds a fully tailored CV from scratch
- `career-ai vault clear` drops the local vector collections for data privacy

### 4.2 Single-Command "Auto-Apply" Agent Pipeline

**Problem:** Running `ats-score`, `cv polish`, `coverletter write`, and `interview prep` individually is repetitive.

**Solution:** A stateful pipeline agent that handles the entire workflow for a specific job target in one execution.

- New command: `career-ai agent apply`
- Creates a dedicated project folder: `output/Company_Role/`
- Generates a final summary report of the full package created

```bash
career-ai agent apply --url <jd_url> --company "Stripe" --role "Backend Engineer"
```

#### 4.2.1 LangGraph Architecture (Recommended)

LangGraph is the recommended orchestration layer for the Auto-Apply pipeline. Unlike standard LangChain, LangGraph is purpose-built for **cyclical, stateful agent workflows** — modelling agent processes as directed graphs of nodes and edges.

**Why LangGraph fits here:**

- Each pipeline step maps cleanly to a **graph node**: `extract_jd` → `ats_score` → `vault_query` → `generate_cv` → `generate_cover_letter` → `generate_interview_prep` → `summarise`
- **Conditional edges** allow failure recovery: if a node fails or produces low-confidence output, the graph routes back to the LLM to fix it before advancing
- **Shared state object** (`AgentState`) is passed between nodes, eliminating the need to re-read files or re-call APIs at each step
- **Checkpointing** via LangGraph's built-in persistence (backed by the existing SQLite DB) enables resumable pipelines — if the run is interrupted mid-way, it can continue from the last completed node

**Proposed graph topology:**

```
[START]
   │
   ▼
extract_jd ──(fail)──► fix_extraction
   │                        │
   ▼                        │
ats_score ◄─────────────────┘
   │
   ▼
vault_query
   │
   ▼
generate_cv ──(low score)──► revise_cv
   │                              │
   ▼                              │
generate_cover_letter ◄───────────┘
   │
   ▼
generate_interview_prep
   │
   ▼
summarise
   │
   ▼
[END]
```

**State schema (example):**

```python
class AgentState(TypedDict):
    jd_text: str
    ats_score: float
    missing_keywords: list[str]
    vault_chunks: list[str]
    cv_draft: str
    cover_letter_draft: str
    interview_prep: str
    errors: list[str]
```

**Integration with existing stack:**

- Nodes call the existing Python functions in `career_ai/core/` — no rewrites needed
- LiteLLM remains the LLM routing layer inside each node
- The existing SQLite DB (`usage.db`) is extended to serve as LangGraph's checkpointer store

---

## 5. Technical Requirements & Dependencies

### Current stack (v1.0)

```
typer[all]>=0.12
pydantic>=2.0
pyyaml>=6.0
python-dotenv>=1.0
litellm>=1.40
tiktoken>=0.7
pdfplumber>=0.11
python-docx>=1.1
markdown>=3.6
reportlab>=4.0
jinja2>=3.1
rich>=13.0
```

### Additions by phase

| Phase | Dependency | Purpose |
|---|---|---|
| 1 | `trafilatura` or `beautifulsoup4` + `requests` | URL scraping |
| 2 | `spacy` or `scikit-learn` | Local ATS keyword matching |
| 2 | `prompt_toolkit` | Interactive chat REPL |
| 2 | SQLite schema migration | Chat history, session memory |
| 3 | `langgraph>=0.2` | Stateful agent pipeline orchestration |
| 3 | `chromadb` | Local vector storage for Career Vault |
| 3 | `sentence-transformers` | Local embeddings (zero token cost) |

> **Note on LangGraph:** `langgraph` is a standalone package with no dependency on the full LangChain stack. Adding it does not pull in `langchain-core` bloat unless explicitly imported.

---

## 6. Project Structure (v2.0)

```
career-ai/
├── career_ai/
│   ├── cli.py                        # Entry point — all CLI commands
│   ├── config.py
│   ├── default_config.yaml
│   ├── core/
│   │   ├── extractor.py              # PDF / DOCX / MD / TXT parsing
│   │   ├── reviewer.py
│   │   ├── polisher.py
│   │   ├── generator.py
│   │   ├── interviewer.py            # NEW — interview prep generation
│   │   ├── ats.py                    # NEW — local ATS keyword scoring
│   │   └── scraper.py                # NEW — URL → JD text extraction
│   ├── llm/
│   │   ├── client.py
│   │   └── tokens.py
│   ├── agent/                        # NEW — Phase 3 agentic layer
│   │   ├── state.py                  # AgentState TypedDict
│   │   ├── nodes.py                  # LangGraph node functions
│   │   ├── graph.py                  # Graph definition and compilation
│   │   └── checkpointer.py          # SQLite-backed LangGraph checkpointer
│   ├── vault/                        # NEW — Phase 3 RAG layer
│   │   ├── ingest.py                 # Chunk, embed, and store documents
│   │   └── query.py                  # Retrieve relevant chunks for a JD
│   └── utils/
│       ├── logging.py
│       └── output.py
└── tests/
    ├── test_cli.py
    ├── test_extractor.py
    ├── test_ats.py                   # NEW
    ├── test_scraper.py               # NEW
    └── test_agent_graph.py           # NEW
```

---

## 7. Next Steps

1. Approve specification phases
2. Initialise `feature/url-scraping` branch (Phase 1 start)
3. Update `.env.example` and `config.yaml` to support new max context limits for Chat Mode and Interview Prep
4. Evaluate `trafilatura` vs `beautifulsoup4` for URL scraping reliability
5. Prototype LangGraph `AgentState` and graph topology before committing to Phase 3 implementation
