from pylib.std import argparse
from pylib.tra.assertions import py_assert_all, py_assert_eq


def run_argparse_extended() -> bool:
    p = argparse.ArgumentParser("x")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--mode", choices=["a", "b"], default="a")
    ns = p.parse_args(["a.py", "-o", "out.cpp", "--pretty", "--mode", "b"])
    checks: list[bool] = []
    checks.append(py_assert_eq(ns.input, "a.py", "input"))
    checks.append(py_assert_eq(ns.output, "out.cpp", "output"))
    checks.append(py_assert_eq(ns.pretty, True, "pretty"))
    checks.append(py_assert_eq(ns.mode, "b", "mode"))
    return py_assert_all(checks, "argparse_extended")


if __name__ == "__main__":
    print(run_argparse_extended())
