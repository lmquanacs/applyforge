# Project Plan: AI-Powered Resume & Cover Letter Assistant

## 1. Executive Summary

A web application designed to help job seekers optimize their applications. Users can upload their resumes to receive AI-driven feedback, paste Job Descriptions (JDs) to generate tailored cover letters, and export the results to PDF.

**Tech Stack:**

| Layer | Technologies |
|---|---|
| Frontend (FE) | ReactJS, TypeScript, Tailwind CSS, Vite |
| Backend (BE) | Python, AWS Lambda, API Gateway |
| Infrastructure | AWS CDK (Python or TypeScript) |
| AI Service | OpenAI API, Anthropic Claude, or Amazon Bedrock |
| Local Testing | LocalStack, aws-cdk-local (cdklocal) |
| Package Manager | pnpm (with Workspaces for monorepo management) |

---

## 2. Feature Breakdown

### A. Resume Upload & Parsing
- **FE:** Drag-and-drop file upload interface (PDF/Docx)
- **BE:** Extract text from the uploaded document using libraries like `PyPDF2` or `pdfplumber`

### B. AI Resume Feedback (Enhancement)
- **FE:** A side-by-side view showing the original resume and AI suggestions
- **BE:** Send parsed resume text to the AI model with a strict prompt:
  > "Act as an expert technical recruiter. Review the following resume, identify weak points, and suggest actionable improvements (e.g., adding metrics, improving action verbs). Return the response in structured JSON format."

### C. Cover Letter Generation
- **FE:** A text area to paste the Job Description (JD)
- **BE:** Combine the parsed user resume and the JD into an AI prompt to generate a highly tailored cover letter

### D. Advanced Resume Enhancement (Rewrite)
- **FE:** "Magic Rewrite" button next to specific bullet points
- **BE:** API endpoint that takes a specific bullet point and context (role) and returns 3 rewritten, ATS-optimized variations

### E. PDF Export
- **FE:** Use a client-side library like `@react-pdf/renderer` or `jspdf` to convert the generated cover letter or enhanced resume back into a cleanly formatted PDF without server overhead

---

## 3. Project Structure

A monorepo structure using pnpm workspaces keeps infrastructure code perfectly synced with application code and shares node modules efficiently.

```
applyforge/
├── pnpm-workspace.yaml
├── package.json
├── docker-compose.yml
├── frontend/                        # React SPA
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── components/
│   └── public/
├── backend/                         # Single Lambda, multi-route
│   ├── requirements.txt
│   └── src/
│       ├── app.py                   # Lambda entry point, registers all routers
│       ├── routers/                 # One file per resource (Powertools Router)
│       │   ├── resumes.py           # POST /resumes/parse, POST /resumes/feedback
│       │   ├── cover_letters.py     # POST /cover-letters
│       │   └── bullets.py          # POST /bullets/rewrite
│       ├── services/                # Business logic, no HTTP concerns
│       │   ├── resume_service.py
│       │   ├── cover_letter_service.py
│       │   └── bullet_service.py
│       └── lib/                     # Shared utilities
│           ├── parser.py            # PDF parsing
│           └── llm/                 # Pluggable LLM abstraction
│               ├── base.py          # Abstract BaseLLMClient
│               ├── bedrock.py       # BedrockClient(BaseLLMClient)
│               ├── openai.py        # OpenAIClient(BaseLLMClient)
│               └── factory.py       # get_llm_client() via LLM_PROVIDER env var
├── infra/                           # AWS CDK (TypeScript)
│   ├── cdk.json
│   ├── bin/main.ts
│   ├── lib/
│   │   ├── backend-stack.ts
│   │   └── frontend-stack.ts
│   └── package.json
└── docs/
```

**Why this structure?**

- **Routers:** Each resource (`resumes`, `cover_letters`, `bullets`) owns its routes via Powertools `Router`, included into the main `APIGatewayRestResolver` in `app.py`.
- **Services:** Pure business logic with no HTTP concerns — easy to unit test.
- **LLM abstraction:** `BaseLLMClient` defines a single `invoke(prompt) -> str` interface. Switch providers by changing the `LLM_PROVIDER` env var (`bedrock` | `openai`) — zero code changes.
- **pnpm Workspaces:** Shared JS/TS tooling across frontend and infra.

### LLM Abstraction Design

```
LLM_PROVIDER=bedrock  →  BedrockClient
LLM_PROVIDER=openai   →  OpenAIClient
```

`factory.py` reads `LLM_PROVIDER` at cold start and returns the appropriate client. All services depend only on `BaseLLMClient`, never on a concrete provider.

---

## 4. Local Testing Strategy

Use `cdklocal` (which interacts with LocalStack) to simulate AWS locally — deploying API Gateway and Lambda to a local Docker container instead of the real AWS cloud.

### Step 1: Set up LocalStack

Create a `docker-compose.yml` in your root directory:

```yaml
version: "3.8"
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
      - "4510-4559:4510-4559"
    environment:
      - SERVICES=lambda,apigateway,s3,iam,cloudformation
      - DEBUG=1
      - DOCKER_HOST=unix:///var/run/docker.sock
    volumes:
      - "${LOCALSTACK_VOLUME_DIR:-./volume}:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
```

### Step 2: Install cdklocal

```bash
pnpm add -g aws-cdk-local aws-cdk
```

### Step 3: Local Development Workflow

**1. Start the Local Cloud:**
```bash
docker-compose up -d
```

**2. Deploy Backend & Infra Locally:**
```bash
cd infra
pnpm install
cdklocal bootstrap
cdklocal deploy BackendStack
```
> LocalStack will print out a local API Gateway URL (e.g., `http://localhost:4566/restapis/<api-id>/prod/_user_request_/`)

**3. Run Frontend Locally:**
```bash
cd frontend
pnpm install
# .env.local -> VITE_API_BASE_URL=http://localhost:4566/restapis/...
pnpm dev
```

### Faster Backend Iteration with CDK Watch

Use the CDK watch feature for fast, iterative development — monitors your code and hot-swaps Lambda assets in LocalStack without a full CloudFormation deployment.

```bash
# Inside the infra/ folder
cdklocal watch
```

> **Pro Tip:** This automatically detects changes in `backend/src/` Python files and rapidly updates the Lambda function in your LocalStack container.

---

## 5. Phased Implementation Plan

### Phase 1: Skeleton & Local Setup (Week 1)
- [ ] Initialize the monorepo structure with `pnpm-workspace.yaml`
- [ ] Set up React + Vite in `frontend/` using `pnpm create vite`
- [ ] Set up a basic "Hello World" Python Lambda in `backend/`
- [ ] Write basic CDK scripts in `infra/` to deploy API Gateway and Lambda
- [ ] Get the end-to-end flow working locally using LocalStack/cdklocal

### Phase 2: Core AI Integration (Week 2)
- [ ] Implement document parsing (PDF to Text) in the Backend
- [ ] Integrate OpenAI/Bedrock APIs
- [ ] Create endpoints: `POST /parse-resume`, `POST /generate-feedback`
- [ ] Build the Frontend UI to upload files and display raw feedback

### Phase 3: Cover Letter & PDF (Week 3)
- [ ] Create the `POST /generate-cover-letter` endpoint
- [ ] Build the JD input form on the Frontend
- [ ] Implement PDF export in React using `@react-pdf/renderer`

### Phase 4: Refinement & Advanced Features (Week 4)
- [ ] Implement the "Magic Rewrite" feature for specific bullet points
- [ ] Refine AI prompts for better quality
- [ ] Add error handling, loading states, and rate limiting (API Gateway Usage Plans)
- [ ] Deploy to actual AWS cloud using standard `cdk deploy`
