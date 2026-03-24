# self_hosted parser signature test: variadic kwargs `**kwargs` is rejected.

def pick(**kwargs: int) -> int:
    return 0

if __name__ == "__main__":
    print(pick(a=1))
