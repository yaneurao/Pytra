from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class PrimeInfo:
    value: int
    factors: List[int]

    @property
    def is_prime(self) -> bool:
        return len(self.factors) == 0 and self.value > 1


def sieve(limit: int) -> List[bool]:
    if limit < 2:
        return [False] * (limit + 1)
    is_prime = [True] * (limit + 1)
    is_prime[0] = False
    is_prime[1] = False

    p = 2
    while p * p <= limit:
        if is_prime[p]:
            for multiple in range(p * p, limit + 1, p):
                is_prime[multiple] = False
        p += 1
    return is_prime


def factorize(n: int) -> List[int]:
    factors = []
    d = 2
    x = n
    while d * d <= x:
        while x % d == 0:
            factors.append(d)
            x //= d
        d += 1 if d == 2 else 2
    if x > 1:
        factors.append(x)
    return factors


def build_prime_infos(limit: int) -> List[PrimeInfo]:
    flags = sieve(limit)
    infos = []
    for n in range(2, limit + 1):
        factors = [] if flags[n] else factorize(n)
        infos.append(PrimeInfo(n, factors))
    return infos


def sliding_window_density(flags: List[bool], width: int = 10) -> List[float]:
    values = [1.0 if v else 0.0 for v in flags]
    out = []
    for i in range(len(values)):
        start = max(0, i - width // 2)
        end = min(len(values), i + width // 2 + 1)
        window = values[start:end]
        out.append(sum(window) / len(window))
    return out


class PrimeAnalyzer:
    def __init__(self, limit: int):
        self.limit = limit
        self.infos = build_prime_infos(limit)

    def largest_gap(self, count: int = 5) -> List[int]:
        primes = [info.value for info in self.infos if info.is_prime]
        gaps = []
        for i in range(1, len(primes)):
            gaps.append((primes[i] - primes[i - 1], primes[i - 1], primes[i]))
        gaps.sort(reverse=True)
        return gaps[:count]

    def composition_counts(self) -> Dict[str, int]:
        buckets = {"prime": 0, "composite": 0, "even": 0, "odd": 0}
        for info in self.infos:
            buckets["odd" if info.value % 2 else "even"] += 1
            if info.is_prime:
                buckets["prime"] += 1
            else:
                buckets["composite"] += 1
        return buckets

    def report(self) -> str:
        flags = [info.is_prime for info in self.infos]
        density = sliding_window_density(flags, width=20)
        rows = []
        rows.append(f"limit={self.limit}, prime_count={sum(flags)}")
        rows.append(f"largest_gaps={self.largest_gap()}")
        rows.append(f"counts={self.composition_counts()}")
        rows.append("density_at=[" + ", ".join(f"{v:.2f}" for v in density[:10]) + "]...")
        return "\n".join(rows)

    def first_n_primes(self, n: int) -> List[int]:
        return [info.value for info in self.infos if info.is_prime][:n]


def main() -> None:
    analyzer = PrimeAnalyzer(limit=120)
    print(analyzer.report())
    print("first_primes:", analyzer.first_n_primes(20))
    for info in analyzer.infos:
        if not info.is_prime and info.value <= 40:
            print(f"{info.value} factors: {info.factors}")


if __name__ == "__main__":
    main()
