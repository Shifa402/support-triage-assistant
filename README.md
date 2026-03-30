# AI-Powered Support Triage Assistant

A runnable Python CLI that satisfies the assessment requirements for a support-triage assistant.

## What this project does

For every incoming query, the assistant:

1. Routes the query into one of five required route types:
   - `KNOWLEDGE_BASE`
   - `TICKET_LOOKUP`
   - `ACCOUNT_LOOKUP`
   - `AMBIGUOUS`
   - `UNSUPPORTED`
2. Uses the correct data source.
3. Returns:
   - a human-readable answer
   - a structured decision object

## Project structure

```text
support_triage_assistant/
├── .env.example
├── README.md
├── requirements.txt
├── data/
│   ├── account_upgrade.md
│   ├── accounts.json
│   ├── api_rate_limits.md
│   ├── integration_setup.md
│   ├── refund_policy.md
│   ├── security_practices.md
│   └── tickets.json
├── examples/
│   └── sample_queries.md
└── src/
    └── support_triage/
        ├── __init__.py
        ├── assistant.py
        ├── cli.py
        ├── data_loader.py
        ├── knowledge_base.py
        ├── router.py
        └── triage.py
```

## Design choices

### 1. Query routing
The router is deterministic and transparent. It uses ticket IDs, entity names, and intent keywords to classify the request before answering.

### 2. Knowledge retrieval
The knowledge base uses lightweight lexical retrieval over the provided `.md` files. That keeps the project easy to run and avoids overengineering for a small dataset.

### 3. Structured data lookups
Ticket and account queries are answered directly from `tickets.json` and `accounts.json`.

### 4. Ambiguity handling
If the system cannot identify a specific ticket, account, or policy topic with enough confidence, it asks a clarifying question.

### 5. Unsupported questions
If the answer is not present in any provided source, the assistant refuses cleanly instead of hallucinating.

### 6. Priority triage
The ranking combines:
- ticket priority
- ticket age
- ticket status
- customer tier
- account health score
- account open ticket count

## Setup

### Option A: Run directly with Python

```bash
cd support-triage-assistant
python -m src.support_triage.cli "What is your refund policy?" --pretty
```

### Option B: Create a virtual environment

```bash
cd support_triage_assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.support_triage.cli "Who is assigned to T-2003?" --pretty
```

## Example commands

```bash
python -m src.support_triage.cli "What is your refund policy?" --pretty
python -m src.support_triage.cli "Who is assigned to T-2003?" --pretty
python -m src.support_triage.cli "When does Acme Corp renew?" --pretty
python -m src.support_triage.cli "Check that ticket for me" --pretty
python -m src.support_triage.cli "Are you HIPAA compliant?" --pretty
python -m src.support_triage.cli "Which issues should the support team handle first today?" --pretty
```

## Example output shape

```json
{
  "route": "TICKET_LOOKUP",
  "confidence": 0.93,
  "used_sources": ["tickets.json"],
  "used_tools": ["ticket_lookup"],
  "needs_clarification": false,
  "final_answer": "Ticket T-2003 is currently unassigned."
}
```

## Requirement mapping to the assessment

### Requirement 1 — Query Routing
Implemented in `router.py`.

### Requirement 2 — Knowledge Base Retrieval
Implemented in `knowledge_base.py` and used by `assistant.py`.

### Requirement 3 — Ticket Lookup
Implemented in `assistant.py` using `tickets.json`.

### Requirement 4 — Account Lookup
Implemented in `assistant.py` using `accounts.json`.

### Requirement 5 — Ambiguity Handling
Implemented in `router.py` and `assistant.py`.

### Requirement 6 — Unsupported Questions
Implemented in `router.py` and `assistant.py`.

### Requirement 7 — Support Priority Triage
Implemented in `triage.py` and surfaced through the assistant.

### Requirement 8 — Structured Decision Output
Every response returns the required decision object.

## Notes

- The implementation is intentionally simple, reliable, and easy to demo.
- The `.env.example` file is included to satisfy the submission requirement and to leave room for an LLM-backed version later.
- This project is optimized for correctness, transparency, and fast delivery rather than UI polish.
