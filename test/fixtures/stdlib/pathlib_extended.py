
from pytra.utils.assertions import py_assert_all, py_assert_eq
from pathlib import Path


def run_pathlib_extended() -> bool:
    root = Path("test/transpile/obj/pathlib_case32")
    root.mkdir(parents=True, exist_ok=True)

    child = root / "values.txt"
    child.write_text("42")

    checks: list[bool] = []
    checks.append(py_assert_eq(child.exists(), True, "exists"))
    checks.append(py_assert_eq(child.name, "values.txt", "name"))
    checks.append(py_assert_eq(child.stem, "values", "stem"))
    checks.append(py_assert_eq((child.parent / "values.txt").exists(), True, "parent_join_exists"))
    checks.append(py_assert_eq(child.read_text(), "42", "read_text"))
    return py_assert_all(checks, "pathlib_extended")

if __name__ == "__main__":
    print(run_pathlib_extended())
