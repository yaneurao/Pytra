def gen(n: int) -> int:
    i: int = 0
    while i < n:
        yield i
        i += 1


def main() -> None:
    total: int = 0
    for v in gen(5):
        total += v
    print(total == 10)


if __name__ == "__main__":
    main()
