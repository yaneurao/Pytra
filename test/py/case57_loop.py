def calc_57(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total = total + v
        else:
            total = total + (v * 2)
    return total


if __name__ == "__main__":
    print(calc_57([1, 2, 3, 4]))
