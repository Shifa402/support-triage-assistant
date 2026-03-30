from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .data_loader import Account, Ticket

REFERENCE_DATE = datetime(2026, 3, 30, tzinfo=timezone.utc)


@dataclass(frozen=True)
class RankedTicket:
    ticket_id: str
    score: float
    reasoning: str


PRIORITY_WEIGHTS = {'urgent': 5, 'high': 4, 'medium': 2, 'low': 1}
TIER_WEIGHTS = {'enterprise': 4, 'pro': 2, 'basic': 1}
STATUS_WEIGHTS = {'open': 2, 'in_progress': 1, 'resolved': -4}


def _ticket_age_days(created_at: str) -> int:
    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    return max((REFERENCE_DATE - created).days, 0)


def rank_tickets(tickets: list[Ticket], accounts: list[Account], top_k: int = 5) -> list[RankedTicket]:
    account_map = {a.customer_name: a for a in accounts}
    ranked: list[RankedTicket] = []
    for ticket in tickets:
        account = account_map.get(ticket.customer_name)
        age_days = _ticket_age_days(ticket.created_at)
        score = 0.0
        score += PRIORITY_WEIGHTS.get(ticket.priority, 0)
        score += TIER_WEIGHTS.get(ticket.customer_tier, 0)
        score += STATUS_WEIGHTS.get(ticket.status, 0)
        score += min(age_days, 10) * 0.35
        if account:
            score += min(account.open_ticket_count, 5) * 0.5
            if account.health_score < 40:
                score += 3
            elif account.health_score < 50:
                score += 2
            elif account.health_score < 65:
                score += 1
        reasoning_parts = [
            f"priority={ticket.priority}",
            f"status={ticket.status}",
            f"age={age_days}d",
            f"tier={ticket.customer_tier}",
        ]
        if account:
            reasoning_parts.append(f"health={account.health_score}")
            reasoning_parts.append(f"open_account_tickets={account.open_ticket_count}")
        ranked.append(RankedTicket(ticket_id=ticket.ticket_id, score=round(score, 2), reasoning=', '.join(reasoning_parts)))

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]
