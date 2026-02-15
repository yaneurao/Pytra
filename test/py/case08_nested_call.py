def inc(x: int) -> int:
    return x + 1


def twice(x: int) -> int:
    return inc(inc(x))


if __name__ == "__main__":
    print(twice(10))
