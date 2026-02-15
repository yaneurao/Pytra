def abs_like(n: int) -> int:
    if n < 0:
        return -n
    else:
        return n


if __name__ == "__main__":
    print(abs_like(-12))
