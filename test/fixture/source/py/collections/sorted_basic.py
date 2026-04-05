from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_sorted_basic() -> bool:
    checks: list[bool] = []

    # sorted list of ints
    nums: list[int] = [3, 1, 4, 1, 5, 9, 2, 6]
    result: list[int] = sorted(nums)
    checks.append(py_assert_eq(result[0], 1, "sorted first"))
    checks.append(py_assert_eq(result[-1], 9, "sorted last"))
    checks.append(py_assert_eq(len(result), 8, "sorted len"))

    # original unchanged
    checks.append(py_assert_eq(nums[0], 3, "original unchanged"))

    # sorted list of strings
    words: list[str] = ["banana", "apple", "cherry"]
    sorted_words: list[str] = sorted(words)
    checks.append(py_assert_eq(sorted_words[0], "apple", "sorted str first"))
    checks.append(py_assert_eq(sorted_words[2], "cherry", "sorted str last"))

    # sorted empty
    empty: list[int] = []
    checks.append(py_assert_eq(len(sorted(empty)), 0, "sorted empty"))

    # sorted already sorted
    already: list[int] = [1, 2, 3]
    checks.append(py_assert_eq(sorted(already)[0], 1, "sorted already first"))

    return py_assert_all(checks, "sorted_basic")


if __name__ == "__main__":
    print(run_sorted_basic())
