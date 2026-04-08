# ApplyForge

AI-Powered Resume & Cover Letter Assistant.

## Prerequisites

- Node.js 18+
- pnpm
- Python 3.11+
- Docker (for LocalStack)

## Quick Start

### 1. Install dependencies

```bash
pnpm install
cd backend && pip install -r requirements.txt
```

### 2. Start LocalStack

```bash
docker-compose up -d
```

### 3. Deploy backend locally

```bash
cd infra
pnpm install
cdklocal bootstrap
cdklocal deploy BackendStack
```

### 4. Run frontend

```bash
cd frontend
# set VITE_API_BASE_URL in .env.local to your LocalStack API Gateway URL
pnpm dev
```

## Project Structure

```
applyforge/
├── frontend/       # React + Vite + TypeScript + Tailwind
├── backend/        # Python Lambda functions
├── infra/          # AWS CDK (TypeScript)
└── docs/           # Project documentation
```
