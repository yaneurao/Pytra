from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


FILE_ID = 39
SCENARIO = "ledger_trace"
SEED = 736


@dataclass
class Entry:
    day: int
    debit: float
    credit: float
    note: str


def create_entries(seed: int) -> List[Entry]:
    out = []
    for day in range(1, 13):
        debit = (seed % 7 + day) * 1.4 if day % 2 == 0 else 0.0
        credit = (seed % 5 + (12 - day)) * 0.9 if day % 3 == 0 else 0.0
        if (seed + day) % 4 == 0:
            debit *= 1.2
        if (seed + day) % 5 == 0:
            credit *= 1.5
        out.append(Entry(day, round(debit, 2), round(credit, 2), f"op_{day}"))
    return out


def month_balance(entries: List[Entry]) -> List[float]:
    bal = 0.0
    out = []
    for e in entries:
        bal += e.credit - e.debit
        out.append(round(bal, 2))
    return out


def by_note(entries: List[Entry]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for e in entries:
        out[e.note] = out.get(e.note, 0.0) + (e.credit - e.debit)
    return out


def drawdown(balance: List[float]) -> float:
    peak = balance[0]
    worst = 0.0
    for v in balance:
        if v > peak:
            peak = v
        draw = peak - v
        if draw > worst:
            worst = draw
    return round(worst, 2)


def stats(entries: List[Entry]) -> Dict[str, float]:
    balances = month_balance(entries)
    return {
        "start": 0.0,
        "end": balances[-1],
        "min": min(balances),
        "max": max(balances),
        "drawdown": drawdown(balances),
    }


def ledger_lines(entries: List[Entry]) -> List[str]:
    b = 0.0
    out = []
    for e in entries:
        b += e.credit - e.debit
        out.append(f"d{e.day:02d} c={e.credit:.2f} d={e.debit:.2f} bal={b:.2f}")
    return out


def category_totals(entries: List[Entry]) -> Dict[str, float]:
    return {
        "cash_in": sum(e.credit for e in entries),
        "cash_out": sum(e.debit for e in entries),
        "net": sum(e.credit - e.debit for e in entries),
    }


def main() -> None:
    entries = create_entries(SEED)
    balances = month_balance(entries)
    print(f"id={FILE_ID} scenario={SCENARIO}")
    print(f"stats={stats(entries)}")
    print(f"note={by_note(entries)}")
    print(f"totals={category_totals(entries)}")
    print("trail=" + " ".join(str(v) for v in balances))
    print("lines=")
    print("\n".join(ledger_lines(entries[:4])))


if __name__ == "__main__":
    main()
