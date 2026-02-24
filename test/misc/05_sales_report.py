from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List


@dataclass
class Record:
    day: int
    product: str
    qty: int
    price: float


def parse_rows(raw: str) -> List[Record]:
    rows = []
    for line in raw.strip().splitlines():
        day, product, qty, price = line.split(",")
        rows.append(Record(int(day), product, int(qty), float(price)))
    return rows


def revenue(record: Record) -> float:
    return record.qty * record.price


def aggregate(records: List[Record]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for row in records:
        totals[row.product] = totals.get(row.product, 0.0) + revenue(row)
    return totals


def best_bad(records: List[Record]) -> Dict[str, str]:
    totals = aggregate(records)
    if not totals:
        return {"best": "", "worst": ""}
    best = max(totals, key=totals.get)
    worst = min(totals, key=totals.get)
    return {"best": best, "worst": worst}


def day_summary(records: List[Record]) -> Dict[int, float]:
    by_day: Dict[int, float] = {}
    for row in records:
        by_day[row.day] = by_day.get(row.day, 0.0) + revenue(row)
    return by_day


def moving_average(values: List[float], window: int) -> List[float]:
    out = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        slice_ = values[start:i + 1]
        out.append(mean(slice_))
    return out


def main() -> None:
    raw = """
1,notebook,3,5.0
1,pencil,8,1.2
2,notebook,1,5.0
2,mouse,2,25.0
3,notebook,5,5.0
3,monitor,1,120.0
4,pencil,10,1.2
4,monitor,1,120.0
5,mouse,1,25.0
"""

    records = parse_rows(raw)
    totals = aggregate(records)
    print("product_totals:", totals)
    print("best_and_worst:", best_bad(records))
    by_day = day_summary(records)
    print("daily_total:", by_day)
    days = sorted(by_day)
    values = [by_day[d] for d in days]
    print("daily_moving_avg:", moving_average(values, 2))


if __name__ == "__main__":
    main()


def _monthly_summary(records: list[Record]) -> list[tuple[int, float]]:
    grouped: dict[int, float] = {}
    for row in records:
        grouped[row.day] = grouped.get(row.day, 0.0) + revenue(row)
    return sorted(grouped.items())


def _extended_sales_demo() -> None:
    raw = """
1,keyboard,2,45.0
1,mouse,4,25.0
2,keyboard,1,45.0
2,monitor,1,120.0
3,mouse,3,25.0
3,camera,2,65.0
4,camera,1,65.0
4,monitor,1,120.0
"""
    records = parse_rows(raw)
    print("extended_totals", aggregate(records))
    print("monthly", _monthly_summary(records))
    print("best_bad", best_bad(records))


if __name__ == "__main__":
    _extended_sales_demo()
