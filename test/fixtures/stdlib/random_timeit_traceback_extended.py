import random
from timeit import default_timer as timer
import traceback


def main() -> None:
    random.seed(7)
    v1: float = random.random()
    v2: int = random.randint(1, 3)
    xs: list[int] = [1, 2, 3, 4]
    ws: list[float] = [0.1, 0.2, 0.3, 0.4]
    picked: list[int] = random.choices(xs, ws)
    picked_k: list[int] = random.choices(xs, ws, 5)
    g1: float = random.gauss(0.0, 1.0)
    random.shuffle(xs)
    t0: float = timer()
    txt: str = traceback.format_exc()
    ok_picked: bool = len(picked) == 1
    for v in picked:
        if not (1 <= v <= 4):
            ok_picked = False
    ok_picked_k: bool = len(picked_k) == 5
    for v in picked_k:
        if not (1 <= v <= 4):
            ok_picked_k = False
    ok_shuffle: bool = (len(xs) == 4) and (1 in xs) and (2 in xs) and (3 in xs) and (4 in xs)
    ok_gauss: bool = g1 == g1
    ok: bool = (
        (0.0 <= v1 < 1.0)
        and (1 <= v2 <= 3)
        and ok_picked
        and ok_picked_k
        and ok_gauss
        and ok_shuffle
        and (t0 >= 0.0)
        and isinstance(txt, str)
    )
    print(ok)


if __name__ == "__main__":
    main()
