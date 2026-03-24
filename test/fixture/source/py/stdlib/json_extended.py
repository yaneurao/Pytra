from pytra.std.json import dumps
from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_json_extended() -> bool:
    checks: list[bool] = []
    s1: str = dumps("abc")
    s2: str = dumps(123)
    s3: str = dumps(True)
    checks.append(py_assert_eq(s1, '"abc"', "str"))
    checks.append(py_assert_eq(s2, "123", "int"))
    checks.append(py_assert_eq(s3, "true", "bool"))
    return py_assert_all(checks, "json_extended")


if __name__ == "__main__":
    print(run_json_extended())
