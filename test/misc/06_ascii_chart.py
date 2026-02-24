from __future__ import annotations

import math
from typing import List


def generate_data(days: int = 30) -> List[float]:
    out = []
    for i in range(days):
        base = 20 + 10 * math.sin(i / 4)
        noise = (i % 5) * 0.8
        out.append(round(base + noise, 2))
    return out


def moving_average(values: List[float], window: int = 5) -> List[float]:
    out = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        out.append(sum(values[start : i + 1]) / (i - start + 1))
    return out


def bars(values: List[float], height: int = 12) -> List[str]:
    min_v = min(values)
    max_v = max(values)
    step = (max_v - min_v) or 1
    levels = " ▁▂▃▄▅▆▇█"
    rows = []
    for v in values:
        ratio = (v - min_v) / step
        idx = int(ratio * (len(levels) - 1))
        rows.append(levels[idx])
    return rows


def print_chart(values: List[float], smooth: List[float]) -> None:
    raw = bars(values)
    flat = bars(smooth)
    print("day 	raw	avg")
    for i, (r, a) in enumerate(zip(raw, flat), 1):
        print(f"{i:02d}\t{r}\t{a}")


def stats(values: List[float]) -> None:
    print(f"count={len(values)} min={min(values):.2f} max={max(values):.2f} avg={sum(values)/len(values):.2f}")
    inc = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
    print(f"increasing_steps={inc}/{len(values)-1}")


def main() -> None:
    values = generate_data()
    smooth = moving_average(values)
    print_chart(values, smooth)
    stats(values)


if __name__ == "__main__":
    main()


def moving_average_delta(values: list[float], window: int = 5) -> list[float]:
    smooth = moving_average(values, window)
    return [curr - prev for curr, prev in zip(smooth[1:], smooth[:-1])] + [0.0]


def describe(values: list[float]) -> None:
    deltas = moving_average_delta(values)
    up = len([d for d in deltas if d > 0])
    down = len([d for d in deltas if d < 0])
    flat = len(deltas) - up - down
    print(f"trend up={up}, down={down}, flat={flat}")


def _ascii_demo() -> None:
    values = generate_data(40)
    smooth = moving_average(values, 7)
    print_chart(values, smooth)
    stats(values)
    describe(smooth)


if __name__ == "__main__":
    _ascii_demo()


def trend_lines(values: list[float]) -> list[str]:
    marks = []
    for i in range(1, len(values)):
        if values[i] > values[i - 1]:
            marks.append("up")
        elif values[i] < values[i - 1]:
            marks.append("down")
        else:
            marks.append("same")
    return marks


def _extended_ascii_demo() -> None:
    values = generate_data(24)
    smooth = moving_average(values, 4)
    deltas = moving_average_delta(values, 4)
    print("trend_hist", {k: trend_lines(values).count(k) for k in ["up", "down", "same"]})
    print("delta_peaks", sorted(deltas)[-3:])
    print("window_minmax", (min(smooth), max(smooth)))


if __name__ == "__main__":
    _extended_ascii_demo()
