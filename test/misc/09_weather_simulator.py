from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import List


@dataclass
class Sample:
    day: int
    temp_c: float
    humidity: int
    wind: float


def build_samples(days: int = 14) -> List[Sample]:
    out: List[Sample] = []
    for d in range(days):
        temp = 18 + (d % 5) * 1.8
        hum = 50 + (d * 3) % 40
        wind = 5 + (d % 3) * 2.2
        out.append(Sample(d + 1, round(temp, 1), hum, round(wind, 1)))
    return out


def avg_temp(samples: List[Sample]) -> float:
    return mean(s.temp_c for s in samples)


def comfort_index(sample: Sample) -> str:
    if sample.temp_c > 28:
        return "warm"
    if sample.temp_c < 10:
        return "cold"
    return "mild"


def max_wind(samples: List[Sample]) -> Sample:
    return max(samples, key=lambda s: s.wind)


def bucket(samples: List[Sample]) -> dict[str, int]:
    counts = {"cold": 0, "mild": 0, "warm": 0}
    for s in samples:
        counts[comfort_index(s)] += 1
    return counts


def main() -> None:
    samples = build_samples()
    print(f"days={len(samples)}")
    print(f"avg_temp={avg_temp(samples):.2f}")
    print(f"hottest={max_wind(samples)}")
    print(f"comfort={bucket(samples)}")
    print("table")
    for s in samples:
        print(f"day={s.day}, temp={s.temp_c}, humidity={s.humidity}, wind={s.wind}")


if __name__ == "__main__":
    main()


def humidity_trend(samples: list[Sample]) -> str:
    deltas = [samples[i].humidity - samples[i - 1].humidity for i in range(1, len(samples))]
    return "rising" if sum(deltas) > 0 else "falling"


def _weather_demo() -> None:
    samples = build_samples(10)
    print("temp_avg", avg_temp(samples))
    print("hottest", max(samples, key=lambda s: s.temp_c))
    print("comfort", bucket(samples))
    print("trend", humidity_trend(samples))


if __name__ == "__main__":
    _weather_demo()


def wind_average(samples: list[Sample]) -> float:
    return sum(s.wind for s in samples) / len(samples)


def comfort_by_day(samples: list[Sample]) -> list[tuple[int, str]]:
    return [(s.day, comfort_index(s)) for s in samples]


def _weather_long_demo() -> None:
    samples = build_samples(14)
    print("wind_avg", wind_average(samples))
    print("comfort_by_day", comfort_by_day(samples))
    print("hottest", max(samples, key=lambda s: s.temp_c))
    print("coldest", min(samples, key=lambda s: s.temp_c))
    print("wind_peak", max(samples, key=lambda s: s.wind))


if __name__ == "__main__":
    _weather_long_demo()
