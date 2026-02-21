import random
from timeit import default_timer as timer
import traceback


def main() -> None:
    random.seed(7)
    v1: float = random.random()
    v2: int = random.randint(1, 3)
    t0: float = timer()
    txt: str = traceback.format_exc()
    ok: bool = (0.0 <= v1 < 1.0) and (1 <= v2 <= 3) and (t0 >= 0.0) and isinstance(txt, str)
    print(ok)


if __name__ == "__main__":
    main()
