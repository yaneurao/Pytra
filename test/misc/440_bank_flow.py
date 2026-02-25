from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import re
from typing import Dict, List, Tuple

SCRIPT_ID = 440
TOPIC = ""bank_flow""
SEED = 3093


@dataclass
class Rule:
    name: str
    pattern: str
    severity: int


def load_rules() -> List[Rule]:
    return [
        Rule("alpha", r"[A-Za-z]", 1),
        Rule("digit", r"[0-9]", 2),
        Rule("space", r"\\s+", 1),
        Rule("symbol", r"[^A-Za-z0-9\s]", 3),
    ]


def score(text: str, rules: List[Rule]) -> Dict[str, int]:
    counts = {r.name: 0 for r in rules}
    for rule in rules:
        counts[rule.name] = len(re.findall(rule.pattern, text))
    return counts


def severity_score(text: str, rules: List[Rule]) -> int:
    counts = score(text, rules)
    return sum(counts[r.name] * r.severity for r in rules)


def split_blocks(text: str) -> List[str]:
    words = re.split(r"\n+", text.strip())
    return [w for w in words if w]


def compress(blocks: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = defaultdict(int)
    for b in blocks:
        tokens = b.split()
        for t in tokens:
            out[t.lower()] += 1
    return dict(Counter(out).most_common(8))


def main() -> None:
    rules = load_rules()
    text = (
        "This synthetic line has digits 1 and 2 plus symbols: #!? "+
        "A lot of spaces and tabs might change the shape. " * ((SEED % 5) + 3)
    )
    blocks = split_blocks(text)
    print(f"{TOPIC}:{SCRIPT_ID} blocks={len(blocks)}")
    print("scores", score(text, rules))
    print("severity", severity_score(text, rules))
    print("tokens", compress(blocks))


if __name__ == "__main__":
    main()



def _probe_sequence(seed: int, count: int = 18) -> list[int]:
    out: list[int] = []
    x = seed
    for _ in range(count):
        x = (x * 31 + 7) % 97
        out.append(x)
    return out


def _running_sum(values: list[float]) -> list[float]:
    total = 0.0
    out: list[float] = []
    for value in values:
        total += value
        out.append(total)
    return out


def _histogram(values: list[float], bins: int = 5) -> dict[str, int]:
    if not values:
        return {}
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return {"constant": len(values)}
    width = (hi - lo) / bins
    out: dict[str, int] = {}
    for value in values:
        idx = int((value - lo) / width)
        if idx == bins:
            idx = bins - 1
        out[f"b{idx}"] = out.get(f"b{idx}", 0) + 1
    return out


def _debug_tail() -> None:
    probe = _probe_sequence(SCRIPT_ID)
    series = [((n % 11) / 7.0) for n in probe]
    rs = _running_sum(series)
    print("extra_probe", probe)
    print("extra_bins", _histogram(series))
    print("extra_running", [round(v, 2) for v in rs])


if __name__ == "__main__":
    _debug_tail()
