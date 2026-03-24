# self_hosted parser signature test: positional-only marker `/` is rejected.

def add(a: int, /, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(2, 3))
