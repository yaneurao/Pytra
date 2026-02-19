from pytra.runtime.assertions import py_assert_all, py_assert_eq


def run_str_slice() -> bool:
    s: str = "abcdefghij"
    checks: list[bool] = []
    checks.append(py_assert_eq(s[:5], "abcde", "slice_prefix"))
    checks.append(py_assert_eq(s[5:], "fghij", "slice_suffix"))
    checks.append(py_assert_eq(s[2:7], "cdefg", "slice_middle"))
    checks.append(py_assert_eq(s[:], "abcdefghij", "slice_all"))
    checks.append(py_assert_eq(s[-3:], "hij", "slice_negative_prefix"))
    return py_assert_all(checks, "str_slice")


if __name__ == "__main__":
    print(run_str_slice())
