# Bank RAG Assistant

A conversational banking assistant that answers questions from two sources: a customer's **own data in SQL Server** (transactions, loans) and **bank policy documents** (English and Arabic PDFs). Each user can only ever see their own data, and that rule is enforced by the database, not by the AI.

> **Status:** working prototype built for learning and demonstration. It is not production banking software (see [Known limitations](#known-limitations)).

---

## Features

- **Login with roles:** customers see only their own data; an admin account can query bank-wide.
- **Dynamic text-to-SQL:** the LLM writes the SQL from the question and the live database schema. There are no hardcoded queries.
- **Privacy enforced by SQL Server Row-Level Security (RLS):** even a badly generated query cannot return another customer's rows.
- **Policy search over PDFs:** hybrid retrieval (vector search + BM25 + reranker) with OCR for scanned pages.
- **Bilingual:** English and Arabic documents share one multilingual index, so you can ask in English about Arabic documents and the reverse. Answers come back in the language of the question.
- **Charts on request:** ask for a bar, line or pie chart and get an interactive Plotly chart next to the text answer.
- **Tables and sources:** query results appear in a table, and policy answers cite the document and page. Admins can also see the generated SQL.
- **Conversation memory:** follow-ups like "who made that repayment?" work.
- **Friendly but focused:** handles small talk and politely declines anything unrelated to banking.

## How it works

```
Streamlit login ─▶ graph.invoke()
        │
reset_turn ─▶ access_check ──(refused)───────────────┐
                   │                                  │
                 route                                │
     ┌─────────┬───┴────┬──────────┐                 │
  sql_node  docs_node  (both,     chitchat_node       │
                       in parallel)                   │
     └─────────┴───┬────┴──────────┘                 │
                   ▼                                  │
          generate_answer ◀───────────────────────────┘
                   │
      text + table + chart + sources
```

1. **Login:** credentials are checked against `gold.users_login`, which returns the customer ID and role. These come only from the login lookup, never from chat text.
2. **Access check:** a customer asking about someone else's account is refused politely.
3. **Routing:** the LLM classifies the question as `sql`, `docs`, `both` or `chitchat`.
4. **SQL path:** the LLM writes a `SELECT`, a validator checks it (SELECT-only, allowed tables), and it runs on a connection whose session context carries the customer ID and role. SQL Server's RLS then filters the rows.
5. **Docs path:** the question is embedded and matched against the policy chunks, then reranked.
6. **Answer:** the LLM turns the results into a friendly reply in the user's language.

## Tech stack

| Area | Tools |
|---|---|
| UI | Streamlit, Plotly, pandas |
| Orchestration | LangGraph (fixed graph with checkpointed memory) |
| LLM | Groq API (`openai/gpt-oss-120b`) |
| Database | SQL Server with Row-Level Security, `mssql-python` driver |
| Document search | ChromaDB, `BAAI/bge-m3` embeddings, BM25, `BAAI/bge-reranker-v2-m3` |
| PDF processing | PyMuPDF, pdfplumber (Arabic), Tesseract OCR (optional) |

## Project structure

```
bank-rag-system/
├── streamlit_app.py            # the web app
├── requirements.txt
├── .env.example
├── .streamlit/config.toml      # theme
├── app/
│   ├── config.py               # reads .env
│   ├── auth/service.py         # verify_login()
│   ├── db/
│   │   ├── connection.py       # get_connection(): sets RLS session context
│   │   ├── schema.py           # schema description for the LLM
│   │   └── sql_validator.py    # SELECT-only and table allowlist checks
│   ├── text_to_sql/
│   │   ├── generator.py        # generate_sql()
│   │   ├── access_check.py     # refuses cross-customer questions
│   │   └── executor.py         # generate_natural_answer()
│   ├── docs_retrieval/
│   │   ├── pdf_extractor.py    # PyMuPDF + OCR fallback
│   │   ├── arabic_extractor.py # glyph-based Arabic extraction
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── ingest.py           # builds the vector index
│   │   └── retriever.py        # hybrid search + reranking
│   ├── graph/
│   │   ├── state.py            # shared state
│   │   ├── nodes.py            # all graph nodes
│   │   ├── build.py            # graph wiring
│   │   ├── history_utils.py
│   │   └── chart_utils.py
│   └── ui/charts.py            # Plotly chart builder
├── scripts/
└── tests/
```

## Prerequisites

- Python 3.11
- SQL Server with TCP/IP enabled and SQL authentication on
- A [Groq](https://console.groq.com) API key (the free tier is enough for development)
- *(Optional)* [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for scanned PDFs. Update the install path in `app/docs_retrieval/pdf_extractor.py`.

## Setup

### 1. Install

```bash
git clone <your-repo-url>
cd bank-rag-system
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```
SQL_CONNECTION_STRING=Server=...;Database=...;UID=...;PWD=...;
GROQ_API_KEY=your_groq_key_here
```

### 3. Prepare the database

The app expects a `gold` schema with `dim_customer`, `dim_loan`, `dim_branch`, `dim_channel`, `dim_date` and `fact_transactions`.

**Login table** (the password column is plaintext for lab use only):

```sql
CREATE TABLE gold.users_login (
  user_id INT IDENTITY(1,1) PRIMARY KEY,
  customer_id VARCHAR(8) NULL,          -- NULL for the admin account
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(128) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',   -- 'user' or 'admin'
  created_at DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME()
);
```

**Row-Level Security.** The app sets `customer_id` and `role` in the connection's `SESSION_CONTEXT`, and these predicates read them:

```sql
CREATE FUNCTION dbo.fn_customerAccessPredicate(@customer_key AS INT)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS fn_result
WHERE EXISTS (
        SELECT 1 FROM gold.dim_customer AS c
        WHERE c.customer_key = @customer_key
          AND c.customer_id = CAST(SESSION_CONTEXT(N'customer_id') AS VARCHAR(8))
      )
   OR CAST(SESSION_CONTEXT(N'role') AS VARCHAR(20)) = 'admin';
GO

CREATE FUNCTION dbo.fn_customerIdAccessPredicate(@customer_id AS VARCHAR(8))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN SELECT 1 AS fn_result
WHERE @customer_id = CAST(SESSION_CONTEXT(N'customer_id') AS VARCHAR(8))
   OR CAST(SESSION_CONTEXT(N'role') AS VARCHAR(20)) = 'admin';
GO

CREATE SECURITY POLICY dbo.CustomerAccessPolicy
ADD FILTER PREDICATE dbo.fn_customerAccessPredicate(customer_key)
    ON gold.fact_transactions,
ADD FILTER PREDICATE dbo.fn_customerIdAccessPredicate(customer_id)
    ON gold.dim_loan
WITH (STATE = ON);
GO
```

Customer ID (not customer key) is used because a customer can have several historical keys in a slowly changing dimension.

> **Recommended:** also protect `gold.dim_customer`, which holds names and emails:
> ```sql
> ALTER SECURITY POLICY dbo.CustomerAccessPolicy
> ADD FILTER PREDICATE dbo.fn_customerIdAccessPredicate(customer_id) ON gold.dim_customer;
> ```

> SQL Server won't let you `ALTER` a function that a security policy uses. Drop the policy, change the function, then recreate the policy.

### 4. Index the policy documents

Put PDFs in `data/policy_docs/` (and Arabic circulars in `data/cbe/`), then run:

```bash
python -m app.docs_retrieval.ingest
```

The first run downloads the embedding and reranker models (a few GB). Re-running is safe: each document is replaced, not duplicated.

### 5. Run

```bash
python -m streamlit run streamlit_app.py
```

Always run commands from the project root, and use `python -m ...` for scripts and tests so imports resolve.

## Example questions

| Question | What happens |
|---|---|
| "How many transactions do I have?" | SQL path |
| "Show me a bar chart of my transactions by type" | SQL path plus a Plotly chart |
| "What is the policy on early loan repayment?" | Document search, with sources |
| "ما هي متطلبات التعرف على هوية العميل إلكترونياً؟" | Arabic question, answered in Arabic |
| "Who has the most loans?" *(admin)* | Bank-wide SQL query |
| "Show me transactions for customer C0006" *(as another customer)* | Politely refused |

## Tests

```bash
python -m tests.test_connection
python -m tests.test_auth
python -m tests.test_text_to_sql
python -m tests.test_graph
python -m tests.test_docs_retrieval
python -m tests.test_live_chat      # interactive terminal chat
```

## Security notes

- Privacy comes from **SQL Server RLS**. The access check and SQL validator are extra layers, not the guarantee.
- `role` and `customer_id` are set once at login and are never taken from chat input.
- The LLM only ever sees an allowlist of tables, and `gold.users_login` is never exposed to it.
- Keep `.env` out of version control. The `.gitignore` already excludes it.

## Known limitations

- **Passwords are stored in plaintext** in the lab login table. Hash them (for example with bcrypt) before any real use.
- **Chat history is held in memory** and is lost when the app restarts.
- **The cross-customer check and chart detection use English patterns only.** RLS still protects the data for Arabic questions, but the friendly refusal message may not appear.
- **Groq's free tier** has per-minute token limits, and available models change over time.
- **`mssql-python` is a preview driver.** `pyodbc` is a mature fallback.
- **One PDF is image-based** and is excluded until OCR with the Arabic language pack is set up.

## Author

Built by Yassin Hannourah · [GitHub](https://github.com/yassinwail)