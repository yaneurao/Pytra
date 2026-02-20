from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_comprehension_dict_set() -> bool:
    xs: list[int] = [1, 2, 3, 4]
    odds_sq: set[int] = {x * x for x in xs if x % 2 == 1}
    even_map: dict[int, int] = {x: x * x for x in xs if x % 2 == 0}

    checks: list[bool] = []
    checks.append(py_assert_eq(len(odds_sq), 2, "len odds_sq"))
    checks.append(py_assert_eq((1 in odds_sq), True, "1 in odds_sq"))
    checks.append(py_assert_eq((9 in odds_sq), True, "9 in odds_sq"))
    checks.append(py_assert_eq(len(even_map), 2, "len even_map"))
    checks.append(py_assert_eq(even_map[2], 4, "even_map[2]"))
    checks.append(py_assert_eq(even_map[4], 16, "even_map[4]"))
    return py_assert_all(checks, "comprehension_dict_set")


if __name__ == "__main__":
    print(run_comprehension_dict_set())
