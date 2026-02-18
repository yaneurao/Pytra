# self_hosted parser signature test: keyword-only marker `*` is accepted.

def add(a: int, *, b: int) -> int:
    return a + b

if __name__ == "__main__":
    print(add(2, b=3))
