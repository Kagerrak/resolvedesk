"""Fixed BM25 candidate over already authorized published chunks, without labels."""

import math
import re
from collections import Counter

STOP_WORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "can",
        "could",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "please",
        "should",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "to",
        "us",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
    ]
)
PARAMETERS = {
    "method": "bm25-v1",
    "k1": 1.2,
    "b": 0.75,
    "tokenizer": "ascii-word-lower-stop-v1",
    "limit": 5,
    "minimum_score_exclusive": 0,
    "distance": "1/(1+bm25_score), not cosine or confidence",
}


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP_WORDS]


def rank(rows, query):
    if not rows:
        return []
    documents = [Counter(tokens(row[0].heading + " " + row[0].content)) for row in rows]
    frequencies = Counter(term for doc in documents for term in doc)
    lengths = [sum(doc.values()) for doc in documents]
    average = sum(lengths) / len(lengths) or 1
    scores = []
    for row, doc, length in zip(rows, documents, lengths, strict=True):
        score = 0.0
        for term in set(tokens(query)):
            count = doc[term]
            if count:
                inverse = math.log(
                    1 + (len(rows) - frequencies[term] + 0.5) / (frequencies[term] + 0.5)
                )
                score += inverse * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * length / average))
        if score > 0:
            scores.append((*row, score))
    scores.sort(key=lambda r: (-r[3], r[2].title, r[0].ordinal, str(r[0].id)))
    return [(chunk, version, doc, 1 / (1 + score)) for chunk, version, doc, score in scores[:5]]
