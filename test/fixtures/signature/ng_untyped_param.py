# self_hosted parser signature test: untyped parameter is rejected.

def twice(x) -> int:
    return x * 2


if __name__ == "__main__":
    print(twice(3))
