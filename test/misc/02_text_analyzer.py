from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import List


@dataclass
class TokenStat:
    token: str
    count: int


class TextAnalyzer:
    def __init__(self, text: str):
        self.text = text
        self.words = self.tokenize(text)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z']+", text.lower())

    def frequency(self, n: int = 10) -> List[TokenStat]:
        counter = Counter(self.words)
        return [TokenStat(token, count) for token, count in counter.most_common(n)]

    def average_length(self) -> float:
        return sum(len(w) for w in self.words) / len(self.words)

    def unique_ratio(self) -> float:
        return len(set(self.words)) / max(1, len(self.words))

    def _ngrams(self, n: int) -> List[str]:
        return [" ".join(self.words[i:i + n]) for i in range(len(self.words) - n + 1)]

    def common_bigrams(self, n: int = 8) -> List[TokenStat]:
        grams = self._ngrams(2)
        counter = Counter(grams)
        return [TokenStat(token, count) for token, count in counter.most_common(n)]

    def common_trigrams(self, n: int = 5) -> List[TokenStat]:
        grams = self._ngrams(3)
        counter = Counter(grams)
        return [TokenStat(token, count) for token, count in counter.most_common(n)]

    def sentiment_guess(self) -> str:
        positive = {"good", "great", "success", "clean", "fast", "bright", "friendly"}
        negative = {"bad", "slow", "hard", "bug", "error", "difficult", "crash"}
        score = sum(1 for w in self.words if w in positive) - sum(1 for w in self.words if w in negative)
        return "positive" if score > 0 else "negative" if score < 0 else "neutral"

    def long_summary(self) -> str:
        top = ", ".join(ts.token for ts in self.frequency(6))
        return (
            f"words={len(self.words)}, unique={len(set(self.words))}, "
            f"avg_len={self.average_length():.2f}, unique_ratio={self.unique_ratio():.2f}, "
            f"sentiment={self.sentiment_guess()}, top={top}"
        )


def main() -> None:
    sample = """
Data analysis is useful when it is done with care. Good metrics and clean data
make products better. A clean and tested pipeline is usually successful.
When errors occur, good logging is critical for fixing slow pipelines.
"""

    analyzer = TextAnalyzer(sample)
    print(analyzer.long_summary())
    print("top_words:", analyzer.frequency(8))
    print("top_bigrams:", analyzer.common_bigrams())
    print("top_trigrams:", analyzer.common_trigrams())


if __name__ == "__main__":
    main()


def _extended_text_demo() -> None:
    corpus = TextAnalyzer(
        "Python scripts are easier to read when names are explicit and functions are small. "
        "Small functions make testing and refactoring easier."
    )
    words = corpus.tokenize(" ".join(corpus.text.split()))
    long_words = sorted(set(words), key=len, reverse=True)
    print("longest_tokens", long_words[:10])
    print("starts_with_p", [w for w in words if w.startswith("p")])
    print("token_lengths", {w: len(w) for w in set(words)})
    print("ngrams2", corpus._ngrams(2)[:5])
    print("ngrams3", corpus._ngrams(3)[:3])
    print("ratio_words", corpus.unique_ratio())


if __name__ == "__main__":
    _extended_text_demo()
