# self_hosted parser signature test: variadic args `*args` is rejected.

def count_all(*args: int) -> int:
    return 0

if __name__ == "__main__":
    print(count_all(1, 2, 3))
