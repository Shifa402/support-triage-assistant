# support-triage-assistant
Agentic AI support assistant that intelligently routes queries, retrieves knowledge, and prioritizes support issues using multi-source data.

# AI Support Triage Assistant

An agentic AI system that intelligently routes, retrieves, and responds to support queries using both structured and unstructured data sources.

## Features

-  Intelligent query routing (Knowledge Base, Tickets, Accounts, Ambiguous, Unsupported)
-  Retrieval-Augmented Generation (RAG) over policy documents
-  Ticket lookup from structured JSON data
-  Account lookup with customer insights
-  Ambiguity detection with clarification handling
-  Safe refusal for unsupported queries
-  Support priority triage based on business logic

## System Capabilities

The assistant can:
- Answer policy and documentation questions
- Retrieve ticket and account information
- Ask clarifying questions when needed
- Refuse unsupported queries safely
- Rank support issues based on urgency and impact

## Tech Stack

- Python
- CLI-based interface
- JSON for structured data
- Markdown knowledge base
- (Optional) LLM / RAG integration

## Example Queries

- What is the refund policy?
- Who is assigned to ticket T-2003?
- When does Acme Corp renew?
- Which tickets are urgent and still open?
- Which issues should be handled first today?
