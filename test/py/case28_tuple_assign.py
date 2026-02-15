def swap_sum_28(a: int, b: int) -> int:
    x: int = a
    y: int = b
    x, y = y, x
    return x + y


if __name__ == "__main__":
    print(swap_sum_28(10, 20))
