from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_bitwise_invert_basic() -> bool:
    x: int = 6
    y: int = 3
    inv_y: int = ~y
    and_mask: int = x & ~y
    or_mask: int = x | ~y
    xor_mask: int = x ^ ~y
    checks: list[bool] = []
    checks.append(py_assert_eq(inv_y, -4, "invert"))
    checks.append(py_assert_eq(and_mask, 4, "and_invert"))
    checks.append(py_assert_eq(or_mask, -2, "or_invert"))
    checks.append(py_assert_eq(xor_mask, -6, "xor_invert"))
    return py_assert_all(checks, "bitwise_invert_basic")


if __name__ == "__main__":
    print(run_bitwise_invert_basic())
