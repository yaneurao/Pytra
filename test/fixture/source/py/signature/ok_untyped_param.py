# self_hosted parser signature test: untyped parameter is accepted as unknown.


def twice(x: int) -> int:
    return x * 2


if __name__ == "__main__":
    print(twice(21))
