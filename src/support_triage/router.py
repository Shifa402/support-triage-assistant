from __future__ import annotations

import re
from dataclasses import dataclass

from .data_loader import Account, Ticket

ROUTES = {
    'KNOWLEDGE_BASE',
    'TICKET_LOOKUP',
    'ACCOUNT_LOOKUP',
    'AMBIGUOUS',
    'UNSUPPORTED',
}


@dataclass(frozen=True)
class RouteDecision:
    route: str
    confidence: float
    rationale: str


class QueryRouter:
    def __init__(self, tickets: list[Ticket], accounts: list[Account], kb_doc_names: list[str]):
        self.tickets = tickets
        self.accounts = accounts
        self.kb_doc_names = kb_doc_names
        self.account_names = [a.customer_name.lower() for a in accounts]

    def route(self, query: str) -> RouteDecision:
        q = query.strip().lower()
        ticket_id_match = re.search(r"\bT-\d{4}\b", query, re.IGNORECASE)

        ticket_keywords = {
            'ticket', 'tickets', 'assigned', 'unassigned', 'priority', 'urgent', 'status',
            'open tickets', 'in progress', 'handle first', 'triage', 'issues should'
        }
        account_keywords = {
            'account', 'accounts', 'customer', 'customers', 'renew', 'renewal', 'plan',
            'health score', 'health', 'open ticket count', 'tier'
        }
        kb_keywords = {
            'refund', 'rate limit', 'limits', 'upgrade', 'downgrade', 'sandbox', 'production',
            'webhook', 'integration', 'security', 'api key', 'billing settings', 'policy'
        }
        unsupported_keywords = {
            'hipaa', 'gdpr', 'on-premise', 'on premise', 'legal policies', 'germany'
        }
        ambiguous_patterns = [
            'check that ticket',
            'what is going on with',
            'look at the integration issue',
            'check this customer',
        ]

        if any(p in q for p in ambiguous_patterns):
            return RouteDecision('AMBIGUOUS', 0.63, 'The request lacks a ticket ID, account name, or concrete policy topic.')

        if any(k in q for k in unsupported_keywords):
            return RouteDecision('UNSUPPORTED', 0.85, 'The request asks for information outside the provided sources.')

        if ticket_id_match or any(k in q for k in ticket_keywords):
            return RouteDecision('TICKET_LOOKUP', 0.93 if ticket_id_match else 0.84, 'The query refers to tickets, ticket status, assignment, or prioritization.')

        if any(name in q for name in self.account_names) or any(k in q for k in account_keywords):
            return RouteDecision('ACCOUNT_LOOKUP', 0.88, 'The query refers to customers, plans, renewals, or account health.')

        if any(k in q for k in kb_keywords):
            return RouteDecision('KNOWLEDGE_BASE', 0.84, 'The query asks about product policy or setup guidance found in the knowledge base.')

        # vague references to known customers without a clear ask
        if any(name.split()[0] in q for name in self.account_names):
            return RouteDecision('AMBIGUOUS', 0.58, 'The query names a customer but the action requested is unclear.')

        return RouteDecision('UNSUPPORTED', 0.55, 'No supported route could be identified from the available data sources.')
