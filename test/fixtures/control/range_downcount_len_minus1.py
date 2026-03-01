# Regression fixture: range(len(xs)-1, -1, -1) must iterate in descending order.


def sum_rev(xs: list[int]) -> int:
    total: int = 0
    for i in range(len(xs) - 1, -1, -1):
        total += xs[i]
    return total


def _case_main() -> None:
    print(sum_rev([1, 2, 3, 4]))


if __name__ == "__main__":
    _case_main()
