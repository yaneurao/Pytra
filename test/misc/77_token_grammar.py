from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict


FILE_ID = 77
SCENARIO = "token_grammar"
SEED = 1382


@dataclass
class TokenRow:
    token: str
    count: int


def normalize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def count_tokens(text: str) -> Counter[str]:
    tokens = normalize(text)
    return Counter(tokens)


def ratio(counter: Counter[str]) -> float:
    total = sum(counter.values())
    return len(counter) / total if total else 0.0


def top_tokens(counter: Counter[str], n: int = 12) -> List[TokenRow]:
    return [TokenRow(tok, cnt) for tok, cnt in counter.most_common(n)]


def build_bigrams(tokens: List[str]) -> List[str]:
    return [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]


def overlap(a: str, b: str) -> int:
    return len(set(a) & set(b))


def sentiment_approx(counter: Counter[str]) -> str:
    pos = {"good", "clear", "robust", "fast", "stable", "clean", "friendly"}
    neg = {"bad", "bug", "slow", "fail", "crash", "fragile", "hard"}
    score = sum(counter[w] for w in pos) - sum(counter[w] for w in neg)
    return "positive" if score > 0 else "negative" if score < 0 else "neutral"


def topic_signals(counter: Counter[str]) -> Dict[str, int]:
    topics = {
        "metrics": {"mean", "count", "stdev", "trend", "window"},
        "systems": {"service", "server", "pipeline", "job", "queue"},
        "quality": {"clean", "tested", "robust", "stable", "audit"},
    }
    return {
        key: sum(counter[w] for w in words)
        for key, words in topics.items()
    }


def build_corpus(seed: int) -> List[str]:
    corp = [
        "Robust systems use stable services and clean logs to avoid brittle deployment failures.",
        "A compact test suite improves quality and keeps metrics trustworthy over time.",
        "The queue backlog stays small when workers stay balanced and backpressure is explicit.",
        "Clean interfaces are easier to read, and readable code usually ships faster.",
    ]
    if seed % 2:
        corp.append("Fast retries and deterministic retries reduce negative user impact during storms.")
    if seed % 3:
        corp.append("Data quality gates fail early when noise grows beyond a comfort threshold.")
    return corp


def long_report(counter: Counter[str]) -> str:
    return (
        f"id={FILE_ID} tokens={sum(counter.values())} unique={len(counter)} "
        f"ratio={ratio(counter):.2f} sentiment={sentiment_approx(counter)}"
    )


class CorpusInspector:
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.text = " ".join(lines)
        self.tokens = normalize(self.text)
        self.counter = Counter(self.tokens)

    def top_bigrams(self, n: int = 6) -> List[TokenRow]:
        bi = Counter(build_bigrams(self.tokens))
        return [TokenRow(tok, cnt) for tok, cnt in bi.most_common(n)]

    def fingerprint(self) -> List[str]:
        head = top_tokens(self.counter, 6)
        return [item.token for item in head]

    def complexity_score(self) -> int:
        return sum(overlap(word, SCENARIO) for word in self.fingerprint())

    def report(self) -> str:
        stats = top_tokens(self.counter, 10)
        return " ".join([
            long_report(self.counter),
            f"topics={topic_signals(self.counter)}",
            f"bigrams={[x.token for x in self.top_bigrams()]}",
            f"complexity={self.complexity_score()}",
        ])


def main() -> None:
    corpus = build_corpus(SEED)
    insp = CorpusInspector(corpus)
    print(insp.report())
    print("fingerprint", insp.fingerprint())
    print("top_tokens", [f"{x.token}:{x.count}" for x in top_tokens(insp.counter, 8)])


if __name__ == "__main__":
    main()
