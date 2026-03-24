from pathlib import Path
import math


def run() -> float:
    p = Path("tmp/a.txt")
    q = p.parent
    n = p.name
    s = p.stem
    x = math.sin(math.pi)
    print(q, n, s, x)
    return x


if __name__ == "__main__":
    run()
