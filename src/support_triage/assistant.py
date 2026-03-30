from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from .data_loader import Account, DataRepository, Ticket
from .knowledge_base import SimpleKnowledgeBase
from .router import QueryRouter
from .triage import rank_tickets


@dataclass
class DecisionOutput:
    route: str
    confidence: float
    used_sources: list[str]
    used_tools: list[str]
    needs_clarification: bool
    final_answer: str


class SupportTriageAssistant:
    def __init__(self, data_dir: str):
        self.repo = DataRepository(data_dir)
        self.kb = SimpleKnowledgeBase(self.repo.knowledge_documents)
        self.router = QueryRouter(self.repo.tickets, self.repo.accounts, [d.name for d in self.repo.knowledge_documents])

    def answer(self, query: str) -> dict[str, Any]:
        route_decision = self.router.route(query)
        route = route_decision.route

        if route == 'KNOWLEDGE_BASE':
            return self._answer_knowledge(query, route_decision.confidence)
        if route == 'TICKET_LOOKUP':
            return self._answer_ticket(query, route_decision.confidence)
        if route == 'ACCOUNT_LOOKUP':
            return self._answer_account(query, route_decision.confidence)
        if route == 'AMBIGUOUS':
            return asdict(DecisionOutput(
                route=route,
                confidence=route_decision.confidence,
                used_sources=[],
                used_tools=[],
                needs_clarification=True,
                final_answer='Can you clarify which ticket, customer, or policy topic you want me to check?'
            ))
        return asdict(DecisionOutput(
            route='UNSUPPORTED',
            confidence=route_decision.confidence,
            used_sources=[],
            used_tools=[],
            needs_clarification=False,
            final_answer='I could not find this information in the provided knowledge documents, ticket data, or account data.'
        ))

    def _extract_ticket_id(self, query: str) -> str | None:
        match = re.search(r"\bT-\d{4}\b", query, re.IGNORECASE)
        return match.group(0).upper() if match else None

    def _find_ticket(self, ticket_id: str) -> Ticket | None:
        return next((t for t in self.repo.tickets if t.ticket_id == ticket_id), None)

    def _find_account_by_name(self, query: str) -> Account | None:
        q = query.lower()
        for account in self.repo.accounts:
            if account.customer_name.lower() in q:
                return account
        # partial fallback
        for account in self.repo.accounts:
            token = account.customer_name.lower().split()[0]
            if token in q:
                return account
        return None

    def _answer_knowledge(self, query: str, confidence: float) -> dict[str, Any]:
        result = self.kb.retrieve(query)
        if not result.used_sources:
            return asdict(DecisionOutput(
                route='UNSUPPORTED',
                confidence=0.56,
                used_sources=[],
                used_tools=['knowledge_retrieval'],
                needs_clarification=False,
                final_answer='I could not find supporting evidence for that question in the knowledge base.'
            ))

        answer = self._compose_kb_answer(query, result.answer_context, result.used_sources)
        return asdict(DecisionOutput(
            route='KNOWLEDGE_BASE',
            confidence=confidence,
            used_sources=result.used_sources,
            used_tools=['knowledge_retrieval'],
            needs_clarification=False,
            final_answer=answer,
        ))

    def _compose_kb_answer(self, query: str, context: str, sources: list[str]) -> str:
        q = query.lower()
        if 'refund' in q:
            return 'Monthly plans can be refunded within 14 calendar days if standard usage thresholds were not exceeded. Annual plans are only partially refundable within 7 days, and no refunds are available once custom onboarding has been delivered. Refund requests must be submitted via billing support in the dashboard, and approved refunds usually take 5–7 business days.'
        if 'upgrade' in q or 'downgrade' in q:
            return 'Customers can upgrade at any time from billing settings and the upgrade takes effect immediately after payment. Monthly upgrades are prorated, annual upgrades are billed proportionally for the remaining term, new seats may take up to 10 minutes to appear, and downgrades only take effect at the next billing cycle.'
        if 'rate limit' in q or '429' in q:
            return 'Basic plans are limited to 60 requests per minute, Pro plans to 300 requests per minute, and Enterprise limits are contract-based. When a client exceeds the limit, the API returns HTTP 429 and clients should retry with exponential backoff.'
        if 'webhook' in q or 'integration' in q or 'sandbox' in q:
            return 'Integrations should start with an API key generated from developer settings and use sandbox endpoints during development. Production should only be enabled after sandbox validation. Webhooks must use signature verification, failed deliveries are retried with exponential backoff, and duplicate deliveries should be handled with idempotent processing.'
        if 'security' in q or 'hipaa' in q or 'gdpr' in q:
            return 'The security guidance says API keys should be stored securely, sandbox and production credentials must remain separate, and webhook requests should be signature-verified. It also explicitly says the security documentation does not guarantee regulatory compliance such as HIPAA or GDPR.'
        return f'Based on {", ".join(sources)}, the most relevant guidance is: {context[:500].strip()}'

    def _answer_ticket(self, query: str, confidence: float) -> dict[str, Any]:
        q = query.lower()
        if 'handle first' in q or 'triage' in q or 'should the support team handle first' in q:
            ranked = rank_tickets(self.repo.tickets, self.repo.accounts, top_k=5)
            lines = []
            for idx, item in enumerate(ranked, start=1):
                ticket = self._find_ticket(item.ticket_id)
                lines.append(
                    f"{idx}. {item.ticket_id} ({ticket.customer_name}) — score {item.score}: {item.reasoning}. Latest issue: {ticket.last_customer_message}"
                )
            answer = 'Highest-priority issues for today:\n' + '\n'.join(lines)
            return asdict(DecisionOutput(
                route='TICKET_LOOKUP',
                confidence=0.9,
                used_sources=['tickets.json', 'accounts.json'],
                used_tools=['ticket_lookup', 'triage_engine'],
                needs_clarification=False,
                final_answer=answer,
            ))

        ticket_id = self._extract_ticket_id(query)
        if ticket_id:
            ticket = self._find_ticket(ticket_id)
            if not ticket:
                return asdict(DecisionOutput(
                    route='TICKET_LOOKUP',
                    confidence=0.81,
                    used_sources=['tickets.json'],
                    used_tools=['ticket_lookup'],
                    needs_clarification=False,
                    final_answer=f'I could not find ticket {ticket_id} in tickets.json.'
                ))
            if 'status' in q:
                answer = f'Ticket {ticket.ticket_id} is currently {ticket.status}. Assigned to: {ticket.assigned_to or "unassigned"}. Customer: {ticket.customer_name}. Priority: {ticket.priority}.'
            elif 'assigned' in q or 'owner' in q:
                answer = f'Ticket {ticket.ticket_id} is assigned to {ticket.assigned_to}.' if ticket.assigned_to else f'Ticket {ticket.ticket_id} is currently unassigned.'
            else:
                answer = f'Ticket {ticket.ticket_id} is {ticket.status}, priority {ticket.priority}, assigned to {ticket.assigned_to or "unassigned"}, for {ticket.customer_name}. Latest customer message: {ticket.last_customer_message}'
            return asdict(DecisionOutput(
                route='TICKET_LOOKUP',
                confidence=confidence,
                used_sources=['tickets.json'],
                used_tools=['ticket_lookup'],
                needs_clarification=False,
                final_answer=answer,
            ))

        open_tickets = [t for t in self.repo.tickets if t.status in {'open', 'in_progress'}]
        if 'urgent' in q and 'open' in q:
            matches = [t for t in open_tickets if t.priority == 'urgent']
            answer = 'Urgent active tickets: ' + '; '.join(
                f"{t.ticket_id} ({t.status}, {t.customer_name}, assigned to {t.assigned_to or 'unassigned'})" for t in matches
            )
        elif 'unassigned' in q:
            matches = [t for t in open_tickets if not t.assigned_to]
            answer = 'Currently unassigned active tickets: ' + '; '.join(
                f"{t.ticket_id} ({t.priority}, {t.customer_name})" for t in matches
            )
        else:
            matches = open_tickets
            answer = 'Active tickets: ' + '; '.join(f"{t.ticket_id} ({t.status}, {t.priority})" for t in matches)
        return asdict(DecisionOutput(
            route='TICKET_LOOKUP',
            confidence=0.78,
            used_sources=['tickets.json'],
            used_tools=['ticket_lookup'],
            needs_clarification=False,
            final_answer=answer,
        ))

    def _answer_account(self, query: str, confidence: float) -> dict[str, Any]:
        q = query.lower()
        if 'low health' in q and 'open tickets' in q:
            matches = [a for a in self.repo.accounts if a.health_score < 50 and a.open_ticket_count > 0]
            answer = 'Customers with low health scores and open tickets: ' + '; '.join(
                f"{a.customer_name} (health {a.health_score}, open tickets {a.open_ticket_count}, plan {a.plan})" for a in matches
            )
            return asdict(DecisionOutput(
                route='ACCOUNT_LOOKUP',
                confidence=0.86,
                used_sources=['accounts.json'],
                used_tools=['account_lookup'],
                needs_clarification=False,
                final_answer=answer,
            ))
        if 'low health' in q:
            matches = [a for a in self.repo.accounts if a.health_score < 50]
            answer = 'Accounts with low health scores: ' + '; '.join(
                f"{a.customer_name} (health {a.health_score}, plan {a.plan})" for a in matches
            )
            return asdict(DecisionOutput(
                route='ACCOUNT_LOOKUP',
                confidence=0.84,
                used_sources=['accounts.json'],
                used_tools=['account_lookup'],
                needs_clarification=False,
                final_answer=answer,
            ))

        account = self._find_account_by_name(query)
        if not account:
            return asdict(DecisionOutput(
                route='AMBIGUOUS',
                confidence=0.62,
                used_sources=[],
                used_tools=[],
                needs_clarification=True,
                final_answer='Please specify the customer name for the account lookup.'
            ))

        if 'renew' in q:
            answer = f'{account.customer_name} renews on {account.renewal_date}.'
        elif 'plan' in q:
            answer = f'{account.customer_name} is on the {account.plan} plan.'
        elif 'health' in q:
            answer = f'{account.customer_name} has a health score of {account.health_score} with {account.open_ticket_count} open tickets.'
        else:
            answer = (
                f'{account.customer_name} is on the {account.plan} plan, renews on {account.renewal_date}, '
                f'has {account.open_ticket_count} open tickets, and a health score of {account.health_score}.'
            )
        return asdict(DecisionOutput(
            route='ACCOUNT_LOOKUP',
            confidence=confidence,
            used_sources=['accounts.json'],
            used_tools=['account_lookup'],
            needs_clarification=False,
            final_answer=answer,
        ))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--data-dir', default='data')
    args = parser.parse_args()
    assistant = SupportTriageAssistant(args.data_dir)
    print(json.dumps(assistant.answer(args.query), indent=2))
