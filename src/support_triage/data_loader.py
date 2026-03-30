from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    status: str
    assigned_to: str | None
    created_at: str
    priority: str
    customer_name: str
    customer_tier: str
    last_customer_message: str


@dataclass(frozen=True)
class Account:
    customer_name: str
    plan: str
    renewal_date: str
    open_ticket_count: int
    health_score: int


@dataclass(frozen=True)
class KnowledgeDocument:
    name: str
    text: str


class DataRepository:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.tickets = self._load_tickets()
        self.accounts = self._load_accounts()
        self.knowledge_documents = self._load_knowledge_documents()

    def _load_json(self, filename: str) -> Any:
        with (self.data_dir / filename).open('r', encoding='utf-8') as f:
            return json.load(f)

    def _load_tickets(self) -> list[Ticket]:
        raw = self._load_json('tickets.json')
        return [Ticket(**row) for row in raw]

    def _load_accounts(self) -> list[Account]:
        raw = self._load_json('accounts.json')
        return [Account(**row) for row in raw]

    def _load_knowledge_documents(self) -> list[KnowledgeDocument]:
        docs = []
        for path in sorted(self.data_dir.glob('*.md')):
            docs.append(KnowledgeDocument(name=path.name, text=path.read_text(encoding='utf-8')))
        return docs
