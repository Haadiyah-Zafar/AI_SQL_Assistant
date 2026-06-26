# Agentic SQL Copilot 🤖

> A production-grade AI agent that converts natural language questions into safe, validated SQL queries — with full schema awareness, RAG-powered context retrieval, and human-in-the-loop approval.

---

## Problem Statement

Most business users can't write SQL, and most SQL tools don't understand intent.

**Agentic SQL Copilot** bridges that gap. You ask a question in plain English — the agent understands your database schema, retrieves relevant context, generates a SQL query, validates it for safety, and (optionally) asks for your approval before executing it.

---

## High-Level Architecture

```text
                   ┌──────────────────────┐
                   │      Frontend        │
                   │  React / Streamlit   │
                   └──────────┬───────────┘
                              │
                        HTTP / REST API
                              │
                   ┌──────────▼───────────┐
                   │       FastAPI        │
                   │      Backend API     │
                   └──────────┬───────────┘
                              │
                    SQL Copilot Agent
                              │
        ┌───────────┬──────────┼───────────┬───────────┐
        │           │          │           │           │
        ▼           ▼          ▼           ▼           ▼
 Schema Tool   RAG Tool   SQL Tool   Validator   Executor
        │                                   │
        └──────────────────────┬────────────┘
                               ▼
                          SQL Database
```

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | React or Streamlit (TBD)          |
| Backend    | FastAPI (Python)                  |
| Agent      | LangGraph / LangChain             |
| RAG        | ChromaDB / FAISS + OpenAI Embeddings |
| LLM        | OpenAI GPT-4o                     |
| Database   | SQLite (dev) → PostgreSQL (prod)  |
| Deployment | Docker + AWS (later phases)       |

---

## Project Structure

```text
agentic-sql-copilot/
│
├── backend/
│   ├── app/          # FastAPI app, routes, dependencies
│   ├── agents/       # SQL Copilot orchestration agent
│   ├── rag/          # Embeddings, vector DB, retrieval
│   ├── tools/        # Schema, SQL, Validation, Execution tools
│   ├── services/     # Business logic (auth, file parsing, logging)
│   ├── prompts/      # All LLM prompts as text files
│   ├── models/       # Pydantic models
│   ├── database/     # DB connection, ORM, migrations
│   └── config/       # Settings, API keys, environment config
│
├── frontend/         # UI (React or Streamlit)
├── docs/             # Architecture diagrams, ER diagrams, design decisions
├── data/             # Sample DB, schema files, seed data
├── docker/           # Dockerfiles, nginx config, deployment files
├── tests/            # API, agent, RAG, and SQL generation tests
├── scripts/          # DB creation, data seeding, embedding generation
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Development Phases

| Phase | Description                        | Status     |
|-------|------------------------------------|------------|
| 1     | Environment Setup                  | ✅ Done    |
| 2     | Architecture & Project Skeleton    | 🔄 Current |
| 3     | Agent Workflow Design              | ⏳ Upcoming |
| 4     | Backend API                        | ⏳ Upcoming |
| 5     | RAG Pipeline                       | ⏳ Upcoming |
| 6     | SQL Agent Implementation           | ⏳ Upcoming |
| 7     | Frontend                           | ⏳ Upcoming |
| 8     | Docker & Deployment                | ⏳ Upcoming |
| 9     | AWS Deployment                     | ⏳ Upcoming |

---

## Getting Started

> ⚠️ Setup instructions will be added as the project progresses.

---

## License

MIT
