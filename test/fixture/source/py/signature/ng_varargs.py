# self_hosted parser signature test: untyped variadic args `*args` is rejected.

def count_all(*args) -> int:
    return 0

if __name__ == "__main__":
    print(count_all(1, 2, 3))
