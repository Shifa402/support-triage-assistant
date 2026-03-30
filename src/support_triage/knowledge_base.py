from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .data_loader import KnowledgeDocument

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]+")
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can', 'do', 'for', 'from', 'how', 'i',
    'if', 'in', 'is', 'it', 'me', 'my', 'of', 'on', 'or', 'our', 'please', 'the', 'this', 'to',
    'what', 'when', 'which', 'who', 'with', 'you', 'your'
}


@dataclass(frozen=True)
class RetrievalResult:
    answer_context: str
    used_sources: list[str]
    scores: list[tuple[str, float]]


class SimpleKnowledgeBase:
    def __init__(self, documents: list[KnowledgeDocument]):
        self.documents = documents
        self.doc_tokens = {doc.name: self._tokenize(doc.text) for doc in documents}
        self.df = Counter()
        for tokens in self.doc_tokens.values():
            for token in set(tokens):
                self.df[token] += 1
        self.total_docs = max(len(documents), 1)

    def _tokenize(self, text: str) -> list[str]:
        return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS]

    def _idf(self, term: str) -> float:
        return math.log((self.total_docs + 1) / (1 + self.df.get(term, 0))) + 1

    def retrieve(self, query: str, top_k: int = 2) -> RetrievalResult:
        q_terms = self._tokenize(query)
        scores: list[tuple[str, float]] = []
        for doc in self.documents:
            doc_terms = self.doc_tokens[doc.name]
            term_freq = Counter(doc_terms)
            score = 0.0
            for term in q_terms:
                score += term_freq.get(term, 0) * self._idf(term)
            # light phrase bonus for title overlap
            filename_terms = self._tokenize(doc.name.replace('_', ' '))
            for term in q_terms:
                if term in filename_terms:
                    score += 1.5
            scores.append((doc.name, score))

        ranked = sorted(scores, key=lambda x: x[1], reverse=True)
        selected = [name for name, score in ranked[:top_k] if score > 0]
        snippets = []
        for name in selected:
            doc = next(d for d in self.documents if d.name == name)
            snippets.append(doc.text.strip())
        context = "\n\n".join(snippets)
        return RetrievalResult(answer_context=context, used_sources=selected, scores=ranked)
