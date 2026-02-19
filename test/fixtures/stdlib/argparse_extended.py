from pylib.std import argparse
from pylib.tra.assertions import py_assert_stdout


def main() -> None:
    p = argparse.ArgumentParser("x")
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--mode", choices=["a", "b"], default="a")
    ns = p.parse_args(["a.py", "-o", "out.cpp", "--pretty", "--mode", "b"])
    print(ns.input)
    print(ns.output)
    print(ns.pretty)
    print(ns.mode)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["a.py", "out.cpp", "True", "b"], _case_main))
