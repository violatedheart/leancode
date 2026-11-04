"""Tiny retrieval examples for common, local code fixes."""
from __future__ import annotations

import math
from .index import tokens

EXAMPLES = [
    ("off-by-one loop last item", "for item in items[:-1]:", "iterate over items; avoid dropping the final element"),
    ("None handling optional empty", "return 0 if value is None else value", "handle None explicitly before arithmetic or access"),
    ("wrong comparison operator boundary", "if count > limit:", "use >= when the boundary value is included"),
    ("missing import name error", "import math", "add the narrow standard-library import used by this function"),
    ("bad API usage keyword argument", "client.get(url, timeout=timeout)", "match the installed API signature and pass named options"),
    ("wrong default mutable list", "def f(items=None):", "use None as the default and allocate a fresh list inside"),
    ("round currency final total", "round(subtotal * (1 - rate), 2)", "round once after all arithmetic, to the currency precision"),
    ("stable unique order", "list(dict.fromkeys(values))", "deduplicate while preserving first-seen order"),
    ("empty average division", "return None if not values else sum(values) / len(values)", "handle empty input before dividing"),
    ("case insensitive trimmed boolean", "value.strip().lower()", "normalize surrounding whitespace and case before parsing"),
    ("fibonacci zero base case", "if n == 0: return 0", "define both base cases before the iteration"),
    ("retry exponential backoff cap", "min(max_ms, base_ms * 2 ** attempt)", "use exponential growth and clamp the result to the cap"),
]


def retrieve(query: str, *, limit: int = 2, max_tokens: int = 250) -> str:
    terms = set(tokens(query))
    corpus = [(task, snippet, edit, tokens(task + " " + snippet + " " + edit)) for task, snippet, edit in EXAMPLES]
    lengths = [len(row[3]) for row in corpus]
    average = sum(lengths) / max(1, len(lengths))
    document_frequency = {term: sum(term in row[3] for row in corpus) for term in terms}
    scored = []
    for task, snippet, edit, words in corpus:
        score = 0.0
        for term in terms:
            frequency = words.count(term)
            if frequency:
                idf = math.log(1 + (len(corpus) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
                score += idf * frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * len(words) / max(average, 1)))
        if score:
            scored.append((score, task, snippet, edit))
    rows = []
    budget = max_tokens * 4
    for _score, task, snippet, edit in sorted(scored, reverse=True)[:limit]:
        row = f"{task}: {snippet} -> {edit}"
        if len(row) > budget:
            row = row[:budget]
        rows.append(row)
        budget -= len(row)
        if budget <= 0:
            break
    return "\n".join(rows)
