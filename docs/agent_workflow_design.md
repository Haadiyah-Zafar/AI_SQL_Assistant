# Agent Workflow Design

## Phase 2 – Module 2

> This document defines how the SQL Copilot Agent thinks, decides, and acts — before we write a single line of agent code.

---

## 1. What Problem Is the Agent Solving?

A user asks a question in plain English.
The agent must:

1. Understand what the user is asking
2. Figure out which database tables are relevant
3. Generate a correct SQL query
4. Make sure the query is safe
5. Optionally ask the user for approval
6. Execute the query
7. Explain the results in plain English

That's 7 steps. Each step is a **decision point** — the agent must decide what to do next based on what just happened.

But **before any of that can happen**, the user must upload their own database.

---

## 2. Database Upload Pipeline (Before the Agent)

The agent doesn't work with a hardcoded database. Users bring their own.
This is a **separate flow** that runs once per database, before any questions are asked.

### 2.1 Upload Flow (Visual)

```
        ┌──────────────────┐
        │   User uploads   │
        │   database file  │
        │ (.db .sqlite     │
        │  .csv .sql)      │
        └────────┬─────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   VALIDATE FILE   │── Invalid? ──► Return error
        │   (type, size,    │   ("Unsupported format" /
        │    corruption)    │    "File too large")
        └────────┬──────────┘
                 │
               Valid
                 │
                 ▼
        ┌───────────────────┐
        │   STORE FILE      │
        │   (save to disk,  │
        │    assign DB ID)  │
        └────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   EXTRACT SCHEMA  │
        │   (tables, cols,  │
        │    types, FKs)    │
        └────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   GENERATE        │
        │   EMBEDDINGS      │
        │   (schema → RAG)  │
        └────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   READY           │
        │   Database is now │
        │   queryable ✅    │
        └───────────────────┘
```

### 2.2 Supported File Types

| File Type | What Happens |
|-----------|-------------|
| `.db` / `.sqlite` | Used directly as a SQLite database |
| `.csv` | Parsed and loaded into a new SQLite database (one table per CSV) |
| `.sql` | Executed against a new SQLite database to create tables & insert data |

For Phase 1, we support SQLite only. PostgreSQL and MySQL support can be added later.

### 2.3 Upload Validation Rules

| Check | Threshold | Error Message |
|-------|-----------|---------------|
| File size | Max 50 MB | "File too large. Maximum size is 50 MB." |
| File extension | `.db`, `.sqlite`, `.csv`, `.sql` | "Unsupported file format." |
| Corruption check | Can SQLite open it? | "The file appears to be corrupted." |
| Empty database | At least 1 table | "This database has no tables." |
| Table count | Max 200 tables | "Database has too many tables for processing." |

### 2.4 Schema Extraction

Once the file is validated, we extract the full schema:

```
For each table:
  - Table name
  - Column names, data types, nullable, default values
  - Primary keys
  - Foreign keys (which table & column they reference)
  - Row count (approximate)
  - Sample data (first 3 rows — helps the LLM understand the data format)
```

This schema is stored as structured data AND as a human-readable text string
(the text version is what gets sent to the LLM).

### 2.5 Embedding Generation

After schema extraction, we generate embeddings for RAG:

```
For each table:
  → Embed: "Table: customers | Columns: id, name, email, created_at
             | Primary Key: id | Foreign Keys: none
             | Sample: (1, 'Alice', 'alice@email.com', '2024-01-15')"
```

These embeddings go into a **vector store** (ChromaDB).
Later, when the user asks a question, we retrieve only the relevant tables.

### 2.6 What This Maps To In Code

```
backend/
├── app/
│   └── routes/
│       └── upload.py            ← POST /api/upload endpoint
│
├── services/
│   ├── file_validator.py        ← Validate file type, size, corruption
│   ├── file_parser.py           ← Parse CSV → SQLite, execute .sql files
│   ├── schema_extractor.py      ← Extract tables, columns, FKs, samples
│   └── database_manager.py      ← Store, list, delete uploaded databases
│
├── rag/
│   └── embeddings.py            ← Generate & store schema embeddings
│
└── database/
    └── connection.py             ← Connect to any uploaded database by ID
```

---

## 3. The Query Workflow (Visual)

Once a database is uploaded and ready, the agent handles questions:

```
  ┌───────────────────────────────────────────────────┐
  │  PREREQUISITE: User has uploaded a database ✅    │
  └───────────────────────┬─────────────────────────  ┘
                          │
         ┌────────────────▼──────────────┐
         │  User sends a question        │
         └────────────────┬──────────────┘
                          │
              ┌───────────▼───────────┐
              │  Database uploaded?   │── No ──► "Please upload a
              └───────────┬───────────┘            database first"
                          │
                        Yes
                          │
                          ▼
                 ┌───────────────┐
                 │   CLASSIFY    │
                 │   INTENT      │──── Off-topic? ──► Respond & END
                 └───────┬───────┘
                         │
                   SQL question
                         │
                         ▼
                 ┌───────────────┐
                 │   RETRIEVE    │
                 │   SCHEMA      │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   RETRIEVE    │
                 │   CONTEXT     │  (RAG: similar queries, docs)
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   GENERATE    │
                 │   SQL         │◄──────────────────────┐
                 └───────┬───────┘                       │
                         │                               │
                         ▼                               │
                 ┌───────────────┐                       │
                 │   VALIDATE    │── Invalid? ───────────┘
                 │   SQL         │   (retry with error feedback)
                 └───────┬───────┘
                         │
                       Valid
                         │
                         ▼
                 ┌───────────────┐
                 │  IS IT A      │
                 │  READ or      │
                 │  WRITE query? │
                 └───┬───────┬───┘
                     │       │
                  READ     WRITE
                     │       │
                     │       ▼
                     │  ┌──────────────┐
                     │  │   HUMAN      │
                     │  │   APPROVAL   │── Rejected? ──► Respond & END
                     │  └──────┬───────┘
                     │         │
                     │      Approved
                     │         │
                     ▼         ▼
                 ┌───────────────┐
                 │   EXECUTE     │── Error? ──► Respond with error
                 │   SQL         │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   EXPLAIN     │
                 │   RESULTS     │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   RESPOND     │
                 │   TO USER     │
                 └───────────────┘
```

---

## 4. Agent State

In LangGraph, the agent carries a **state object** through every step.
Think of it as a clipboard that each step reads from and writes to.

Here's what our agent needs to remember at any point:

```
┌─────────────────────────────────────────────────────────┐
│                     AGENT STATE                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  user_question          "Show me top 5 customers"       │
│  intent                 "sql_query"                     │
│  conversation_history   [previous messages...]          │
│                                                         │
│  database_id            "abc123"  (uploaded DB ID)      │
│  database_name          "sales_data.db" (original name) │
│  schema_context         "Table: customers (id, name.."  │
│  rag_context            "Similar query: SELECT..."      │
│                                                         │
│  generated_sql          "SELECT name FROM customers.."  │
│  is_read_query          true                            │
│  validation_result      { valid: true, issues: [] }     │
│  retry_count            0                               │
│                                                         │
│  approval_status        "approved" / "rejected" / null  │
│                                                         │
│  query_result           [{ name: "Alice" }, ...]        │
│  explanation            "Here are the top 5 customers"  │
│  error                  null                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

The `database_id` comes from the upload pipeline — it's how the agent knows
which database to query.

Each step (node) reads what it needs from this state and writes its output back.

---

## 5. Nodes (Steps) — Detailed Design

### 5.1 Classify Intent

**Purpose:** Determine what the user is actually asking for.

**Input from state:** `user_question`, `conversation_history`

**Output to state:** `intent`

**Possible intents:**

| Intent | Example | What happens next |
|--------|---------|-------------------|
| `sql_query` | "Show me all orders from last month" | Continue to Retrieve Schema |
| `schema_question` | "What tables do I have?" | Retrieve Schema → Explain directly |
| `follow_up` | "Now sort that by date" | Retrieve previous context → Generate SQL |
| `off_topic` | "What's the weather?" | Respond politely & END |
| `clarification_needed` | "Show me the thing" | Ask user to clarify & END |

**Why this matters:**
Without this step, the agent would try to generate SQL for "hello" or "thanks".

---

### 5.2 Retrieve Schema

**Purpose:** Find the relevant tables and columns for the user's question.

**Input from state:** `user_question`, `database_id`

**Output to state:** `schema_context`

**How it works:**
1. Look up which database is connected
2. Pull the full schema (tables, columns, types, relationships)
3. If the database is large, use embeddings to find only the *relevant* tables

**Example output:**
```
Table: customers
  - id (INTEGER, PRIMARY KEY)
  - name (TEXT)
  - email (TEXT)
  - created_at (DATETIME)

Table: orders
  - id (INTEGER, PRIMARY KEY)
  - customer_id (INTEGER, FOREIGN KEY → customers.id)
  - total (DECIMAL)
  - order_date (DATETIME)
```

**Design decision:** For small databases (< 15 tables), send the full schema.
For large databases, use RAG to retrieve only relevant tables.

---

### 5.3 Retrieve Context (RAG)

**Purpose:** Find similar past queries, documentation, or business rules that help generate better SQL.

**Input from state:** `user_question`, `schema_context`

**Output to state:** `rag_context`

**What gets retrieved:**
- Similar natural language → SQL pairs (few-shot examples)
- Business rules ("revenue = price × quantity - discount")
- Column descriptions ("status 1 = active, 2 = inactive")

**Why this matters:**
Without RAG, the agent might generate `SELECT * FROM users WHERE active = 'yes'` when the actual column uses `1` and `0`.

---

### 5.4 Generate SQL

**Purpose:** Use the LLM to convert the natural language question into a SQL query.

**Input from state:** `user_question`, `schema_context`, `rag_context`, `conversation_history`

**Output to state:** `generated_sql`, `is_read_query`

**The prompt will include:**
1. System instructions ("You are a SQL expert...")
2. The database schema
3. RAG context (examples, business rules)
4. Conversation history (for follow-up queries)
5. The user's question

**The LLM returns:**
- The SQL query
- Whether it's a READ (SELECT) or WRITE (INSERT/UPDATE/DELETE) operation

---

### 5.5 Validate SQL

**Purpose:** Check the generated SQL for safety and correctness BEFORE execution.

**Input from state:** `generated_sql`, `schema_context`

**Output to state:** `validation_result`, updated `retry_count`

**What it checks:**

| Check | What it catches |
|-------|-----------------|
| **Syntax validation** | Malformed SQL |
| **Table/column existence** | References to tables that don't exist |
| **Dangerous operations** | `DROP TABLE`, `TRUNCATE`, `DELETE` without WHERE |
| **Query complexity** | Queries that would scan millions of rows |
| **Injection patterns** | SQL injection attempts (from malicious input) |

**If validation fails:**
- Increment `retry_count`
- Send the error message back to the Generate SQL step
- The LLM tries again with feedback about what went wrong
- **Maximum 3 retries**, then respond with an error

---

### 5.6 Human Approval (Conditional)

**Purpose:** For WRITE operations, ask the user to approve before executing.

**When it triggers:**
- `INSERT`, `UPDATE`, `DELETE` operations → **Always ask**
- `SELECT` operations → **Skip this step** (safe to run)

**What the user sees:**
```
I've generated this query:

  UPDATE customers SET status = 'inactive'
  WHERE last_order_date < '2024-01-01'

This will affect approximately 342 rows.

Do you want to execute this? [Approve] [Reject] [Modify]
```

**If rejected:** End the workflow, optionally let the user modify.
**If approved:** Continue to Execute.

---

### 5.7 Execute SQL

**Purpose:** Run the validated (and optionally approved) query against the database.

**Input from state:** `generated_sql`, `database_id`

**Output to state:** `query_result` or `error`

**Safety measures:**
- Query timeout (30 seconds max)
- Row limit for SELECT (return max 1000 rows)
- Transaction wrapping for WRITE operations (rollback on error)

---

### 5.8 Explain Results

**Purpose:** Convert raw query results into a natural language explanation.

**Input from state:** `user_question`, `generated_sql`, `query_result`

**Output to state:** `explanation`

**Example:**
```
User asked: "Who are our top 5 customers by revenue?"

SQL: SELECT name, SUM(total) as revenue FROM customers
     JOIN orders ON customers.id = orders.customer_id
     GROUP BY name ORDER BY revenue DESC LIMIT 5

Result explanation:
"Your top 5 customers by total revenue are:
 1. Acme Corp — $124,500
 2. TechStart — $98,200
 3. GlobalFin — $87,300
 4. DataFlow — $76,100
 5. CloudNet — $65,800

Acme Corp leads with 27% more revenue than the second-highest customer."
```

---

## 6. Routing Logic (Edges)

These are the decision rules that connect nodes:

```
classify_intent
  ├── intent == "sql_query"            → retrieve_schema
  ├── intent == "schema_question"      → retrieve_schema
  ├── intent == "follow_up"            → retrieve_schema
  ├── intent == "off_topic"            → respond (END)
  └── intent == "clarification_needed" → respond (END)

retrieve_schema
  └── always                           → retrieve_context

retrieve_context
  └── always                           → generate_sql

generate_sql
  └── always                           → validate_sql

validate_sql
  ├── valid == true, is_read_query     → execute_sql
  ├── valid == true, is_write_query    → human_approval
  ├── valid == false, retries < 3      → generate_sql (retry)
  └── valid == false, retries >= 3     → respond with error (END)

human_approval
  ├── approved                         → execute_sql
  └── rejected                         → respond (END)

execute_sql
  ├── success                          → explain_results
  └── error                            → respond with error (END)

explain_results
  └── always                           → respond (END)
```

---

## 7. Error Handling Strategy

Every node can fail. Here's how we handle each:

| Node | Failure | Recovery |
|------|---------|----------|
| **Upload: Validate File** | Bad file type / too large | Return clear error with supported formats |
| **Upload: Extract Schema** | Corrupted database | Return error: "File appears corrupted" |
| **Upload: Generate Embeddings** | Embedding API failure | Retry; if persistent, store schema without embeddings (RAG disabled) |
| Classify Intent | LLM timeout | Default to `sql_query` and try |
| Retrieve Schema | No database uploaded | Return error: "Please upload a database first" |
| Retrieve Context | Vector DB empty | Continue without RAG context (still works, just less accurate) |
| Generate SQL | LLM returns invalid SQL | Retry with validation feedback (up to 3 times) |
| Validate SQL | All retries exhausted | Return error: "I couldn't generate a valid query for this question" |
| Human Approval | User doesn't respond | Timeout after 5 minutes, cancel the query |
| Execute SQL | Database error | Return the error message with explanation |
| Explain Results | LLM timeout | Return raw results without explanation |

---

## 8. What Maps to Code

Here's how this design maps to our folder structure:

```
backend/
│
├── app/
│   └── routes/
│       ├── upload.py              ← POST /api/upload (file upload endpoint)
│       ├── query.py               ← POST /api/query (ask a question)
│       └── databases.py           ← GET /api/databases (list uploaded DBs)
│
├── services/
│   ├── file_validator.py          ← Validate file type, size, corruption
│   ├── file_parser.py             ← CSV → SQLite, execute .sql files
│   ├── schema_extractor.py        ← Extract tables, columns, FKs, samples
│   └── database_manager.py        ← Store, list, delete uploaded databases
│
├── agents/
│   └── sql_copilot_agent.py       ← The LangGraph graph definition
│                                     (nodes, edges, state)
│
├── tools/
│   ├── schema_tool.py             ← Retrieve Schema node
│   ├── rag_tool.py                ← Retrieve Context node
│   ├── sql_generator_tool.py      ← Generate SQL node
│   ├── sql_validator_tool.py      ← Validate SQL node
│   └── sql_executor_tool.py       ← Execute SQL node
│
├── prompts/
│   ├── classify_intent.txt        ← Prompt for intent classification
│   ├── generate_sql.txt           ← Prompt for SQL generation
│   ├── validate_sql.txt           ← Prompt for validation
│   └── explain_results.txt        ← Prompt for explanation
│
├── models/
│   ├── agent_state.py             ← The AgentState Pydantic model
│   ├── query_models.py            ← SQLResponse, ValidationResult, etc.
│   ├── upload_models.py           ← UploadResponse, DatabaseInfo, etc.
│   └── api_models.py              ← Request/Response models for the API
│
├── rag/
│   ├── embeddings.py              ← Generate embeddings from schema
│   ├── vector_store.py            ← ChromaDB / FAISS setup
│   └── retriever.py               ← Retrieve relevant context
│
├── database/
│   ├── connection.py              ← Connect to any uploaded DB by ID
│   └── executor.py                ← Safe query execution with limits
│
└── config/
    └── settings.py                ← LLM model, timeouts, retry limits,
                                      upload limits, file storage path
```

Every file has a clear, single responsibility.

---

## 9. LangGraph Representation

For reference — this is roughly what the LangGraph code will look like:

```
StateGraph(AgentState)
│
├── add_node("classify",    classify_intent)
├── add_node("schema",      retrieve_schema)
├── add_node("rag",         retrieve_context)
├── add_node("generate",    generate_sql)
├── add_node("validate",    validate_sql)
├── add_node("approve",     human_approval)
├── add_node("execute",     execute_sql)
├── add_node("explain",     explain_results)
│
├── set_entry_point("classify")
│
├── add_conditional_edges("classify", route_after_classify)
├── add_edge("schema",   "rag")
├── add_edge("rag",       "generate")
├── add_edge("generate",  "validate")
├── add_conditional_edges("validate", route_after_validate)
├── add_conditional_edges("approve",  route_after_approve)
├── add_conditional_edges("execute",  route_after_execute)
├── add_edge("explain",   END)
```

We'll implement this once we start coding the agent.

---

## 10. Key Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Database source | User uploads their own file | Dynamic — works with any database, not hardcoded |
| Supported formats | `.db`, `.sqlite`, `.csv`, `.sql` | Covers most common data formats |
| Upload size limit | 50 MB | Large enough for real use, small enough to process quickly |
| Storage strategy | Save uploaded files to `data/uploads/` with unique ID | Keeps files organized, supports multiple databases per user |
| Schema retrieval strategy | Full schema for small DBs, RAG for large | Simplicity for common case, scalability for edge case |
| Validation approach | Rule-based + LLM | Rules catch obvious issues fast; LLM catches semantic issues |
| Human approval trigger | Only for WRITE queries | READ queries are safe, don't slow down the user |
| Retry limit | 3 attempts | Enough to self-correct, not enough to waste money |
| Result row limit | 1000 rows | Prevents memory issues, UI can paginate later |
| Prompt storage | External .txt files | Easy to iterate on prompts without touching Python code |

---

## 11. The Complete User Journey

Putting it all together — this is the full experience:

```
 ① User opens the app
          │
 ② User uploads a database file (.db, .csv, .sql)
          │
 ③ System validates → extracts schema → generates embeddings
          │
 ④ User sees: "Database ready! Found 8 tables. Ask me anything."
          │
 ⑤ User types: "What were the top 5 products last month?"
          │
 ⑥ Agent: classify → retrieve schema → RAG → generate SQL → validate
          │
 ⑦ Agent shows the SQL query and result in plain English
          │
 ⑧ User asks follow-up: "Now break that down by region"
          │
 ⑨ Agent uses conversation history + schema to generate new query
          │
 ⑩ Repeat...
```

---

## 12. What's Next

With this workflow designed, we now know exactly:
- What each file will do
- How data flows between components
- Where decisions are made
- What errors to handle

**Next module:** We start coding, beginning with:
1. Sample database + upload script (`scripts/` + `data/`)
2. FastAPI backend shell with upload endpoint (`backend/app/`)
3. Schema extraction service (`backend/services/`)
4. Building the agent tools one by one (`backend/tools/`)
