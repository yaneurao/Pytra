import random
from pytra.std import math


class TinySampler:
    def __init__(self, vocab_size: int) -> None:
        self.vocab_size: int = vocab_size
        self.weights: list[float] = []
        i: int = 0
        while i < vocab_size:
            self.weights.append(float(i + 1))
            i += 1

    def draw(self, k: int) -> list[int]:
        ids: list[int] = []
        choices_base: list[int] = []
        for i in range(self.vocab_size):
            choices_base.append(i)
        ids = random.choices(choices_base, self.weights, k)
        random.shuffle(ids)
        return ids


def main() -> None:
    random.seed(42)
    sampler: TinySampler = TinySampler(6)
    ids: list[int] = sampler.draw(4)
    noise: float = random.gauss(0.0, 1.0)
    scale: float = math.sqrt(float(len(ids)))
    ok_ids: bool = len(ids) == 4
    for v in ids:
        if not (0 <= v < 6):
            ok_ids = False
    ok: bool = ok_ids and (noise == noise) and (scale > 0.0)
    print(ok)


if __name__ == "__main__":
    main()
