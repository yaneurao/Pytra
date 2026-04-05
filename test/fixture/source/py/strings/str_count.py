from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_str_count() -> bool:
    s: str = "hello world hello"
    checks: list[bool] = []

    checks.append(py_assert_eq(s.count("hello"), 2, "count hello"))
    checks.append(py_assert_eq(s.count("world"), 1, "count world"))
    checks.append(py_assert_eq(s.count("xyz"), 0, "count missing"))
    checks.append(py_assert_eq(s.count("l"), 5, "count single char"))
    checks.append(py_assert_eq("aaa".count("a"), 3, "count all same"))
    checks.append(py_assert_eq("".count("x"), 0, "count empty string"))

    return py_assert_all(checks, "str_count")


if __name__ == "__main__":
    print(run_str_count())
