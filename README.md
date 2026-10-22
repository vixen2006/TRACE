# TRACE — Engineering Memory

*Your work. Your evidence. Your impact.*

> A verified record of what you built, what changed, and what still needs attention.

TRACE is a single, tool-using AI agent with persistent engineering memory, evidence verification, and structured report generation. It transforms scattered engineering activity into trusted, source-linked contribution records.

## What It Does

- **Engineering Activity Intelligence** — Investigates pull requests, commits, reviews, and issues.
- **Evidence-Backed Contributions** — Links every contribution claim to verifiable source records.
- **Accurate Attribution** — Distinguishes completed work from attempted work, and individual contributions from team activity.
- **Persistent Engineering Memory** — Maintains a structured history of projects, contributions, decisions, and outcomes.
- **AI-Generated Reports** — Produces weekly summaries, one-to-one talking points, and performance review material.
- **Interview Preparation** — Generates evidence-backed engineering stories from real project history.
- **Data Export** — Exports engineering activity and contribution records to CSV.

## Architecture

TRACE uses a bounded, tool-calling AI agent to investigate engineering activity, verify evidence, and generate structured reports.

```text
User Request
     |
     v
Agent Orchestrator
     |
     v
LLM Tool Selection
     |
     v
GitHub API / Evidence Search
     |
     v
Data Normalization & Validation
     |
     v
Evidence-Linked Contribution Records
     |
     v
Structured Report Generation
     |
     v
Engineering Dashboard & Exports
```

The agent can call tools repeatedly to investigate missing or conflicting evidence. Deterministic validation rules handle attribution, duplicate detection, and activity status; the LLM handles flexible investigation, classification, and summarization.

Every generated contribution claim must reference supporting evidence. Unsupported claims are flagged rather than presented as verified facts.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Visualization | Recharts |
| Backend API | FastAPI, Pydantic |
| Agent | Tool-calling LLM, bounded execution loop |
| Database | PostgreSQL |
| Authentication | GitHub OAuth |
| Integrations | GitHub REST API / GraphQL API |
| Background Processing | Scheduled synchronization, background workers |
| Optional Semantic Search | pgvector |

## Project Structure

```text
trace/
├── frontend/               # Next.js application
│   ├── app/
│   ├── components/
│   ├── hooks/
│   └── lib/
├── backend/                # FastAPI service and AI agent
│   ├── app/
│   │   ├── api/
│   │   ├── agent/
│   │   ├── core/
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── migrations/
│   └── tests/
├── docs/                   # Architecture, schema, API contracts
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.11+
- PostgreSQL
- A GitHub OAuth application
- An API key for a tool-calling LLM provider

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd trace
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Configure the required values in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/trace

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

LLM_API_KEY=
LLM_MODEL=
```

Use your actual credentials locally. Never commit `.env` or expose secrets in frontend environment variables.

### 3. Start the backend

```bash
cd backend

python -m venv venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API documentation will be available at:

`http://localhost:8000/docs`

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will typically be available at:

`http://localhost:3000`

Ensure PostgreSQL is running, the database schema has been migrated, and the OAuth callback URL matches your GitHub application configuration before connecting an account.

## Design System

TRACE uses a minimal black, white, and red interface designed for a focused engineering workflow.

| Design Token | Value | Usage |
|---|---|---|
| Background | `#090909` | Main canvas |
| Surface | `#141414` | Cards and panels |
| Elevated Surface | `#1D1D1D` | Menus and overlays |
| Border | `#303030` | Dividers and outlines |
| Accent | `#E32936` | Actions, active states, evidence gaps |
| Primary Text | `#F5F5F5` | Headings and content |
| Secondary Text | `#A3A3A3` | Metadata and supporting text |

**Typography:** Inter or Geist for interface text; JetBrains Mono for commit hashes, identifiers, timestamps, and technical metadata.

## Development Roadmap

### Phase 1 — GitHub MVP

- [ ] GitHub OAuth integration
- [ ] Repository selection and activity synchronization
- [ ] Pull request, commit, review, and issue ingestion
- [ ] Persistent engineering activity database
- [ ] Evidence-linked contribution records
- [ ] Deterministic attribution and status validation
- [ ] Single-agent orchestration and tool calling
- [ ] Weekly engineering report generation
- [ ] Dashboard and activity explorer
- [ ] CSV export
- [ ] Automated tests for duplicates, reverted PRs, and unsupported claims

### Phase 2 — Engineering Intelligence

- [ ] Persistent project-level contribution history
- [ ] One-to-one and performance review reports
- [ ] Evidence-backed interview story generation
- [ ] Semantic search using pgvector, if needed
- [ ] Improved evidence-gap detection

### Phase 3 — Additional Integrations

- [ ] Slack integration
- [ ] Jira integration
- [ ] Documentation platform integration
- [ ] Cross-source evidence linking
- [ ] Advanced reporting and analytics

## Trust & Safety

TRACE is designed around verifiable engineering evidence.

- Every contribution claim should link to its supporting sources.
- Merged work must not automatically be described as deployed.
- Reverted work must not be counted as successful shipped work without appropriate qualification.
- Individual ownership must not be inferred from team activity alone.
- Retrieved content is treated as untrusted data, not as instructions for the agent.
- Source access is governed by authorization and least-privilege permissions.
- Sensitive data and credentials must be protected.
- External publication or sharing requires appropriate user approval.

## Core Principle 

**TRACE does not measure engineering impact by activity volume alone. It builds an evidence-backed record of what happened, what changed, and what can actually be demonstrated.**

## Development Status

TRACE is under active development. Features in the roadmap are planned until implemented and tested.

---

