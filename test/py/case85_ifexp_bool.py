def pick_85(a: int, b: int, flag: bool) -> int:
    c: int = a if (flag and (a > b)) else b
    return c


if __name__ == "__main__":
    print(pick_85(10, 3, True))
