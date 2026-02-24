from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import List


@dataclass
class Unit:
    name: str
    hp: int
    atk: int
    spd: int


def attack(attacker: Unit, defender: Unit, rng: Random) -> str:
    hit = max(1, int(attacker.atk * rng.uniform(0.6, 1.4)))
    defender.hp = max(0, defender.hp - hit)
    return f"{attacker.name} hits {defender.name} for {hit}"


def turn_order(team: List[Unit]) -> List[Unit]:
    return sorted(team, key=lambda u: u.spd, reverse=True)


def round_tick(a: List[Unit], b: List[Unit], rng: Random, log: List[str]) -> bool:
    order = turn_order(a + b)
    for unit in order:
        if unit.hp <= 0:
            continue
        foes = b if unit in a else a
        foe = [u for u in foes if u.hp > 0]
        if not foe:
            return True
        target = rng.choice(foe)
        log.append(attack(unit, target, rng))
    return False


def alive(units: List[Unit]) -> bool:
    return any(u.hp > 0 for u in units)


def main() -> None:
    rng = Random(42)
    team_a = [Unit("knight", 45, 11, 5), Unit("archer", 28, 8, 8)]
    team_b = [Unit("orc", 40, 10, 6), Unit("goblin", 22, 7, 7)]
    log: List[str] = []

    for turn in range(1, 8):
        if not alive(team_a) or not alive(team_b):
            break
        log.append(f"-- turn {turn} --")
        if round_tick(team_a, team_b, rng, log):
            break

    winner = "A" if alive(team_a) and not alive(team_b) else "B" if alive(team_b) and not alive(team_a) else "draw"
    print("winner", winner)
    for line in log:
        print(line)


if __name__ == "__main__":
    main()


def summary(unit: Unit) -> tuple[str, int]:
    return (unit.name, unit.hp)


def _battle_report(a: list[Unit], b: list[Unit]) -> dict[str, str]:
    return {"a": max((u for u in a if u.hp > 0), key=lambda u: u.hp).name if any(u.hp > 0 for u in a) else "none",
            "b": max((u for u in b if u.hp > 0), key=lambda u: u.hp).name if any(u.hp > 0 for u in b) else "none"}


def _battle_demo() -> None:
    rng = Random(7)
    team_a = [Unit("hero", 30, 9, 6)]
    team_b = [Unit("villain", 33, 10, 5)]
    log = []
    for _ in range(3):
        if not alive(team_a) or not alive(team_b):
            break
        round_tick(team_a, team_b, rng, log)
    print("battle_log")
    print("\n".join(log))
    print("summary", _battle_report(team_a, team_b))


if __name__ == "__main__":
    _battle_demo()
