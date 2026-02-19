from pylib.std import re
from pylib.tra.assertions import py_assert_stdout


def main() -> None:
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", "x = 1")
    if m is None:
        print("None")
        return
    print(m.group(1))
    print(m.group(2))
    out = re.sub(r"\s+", " ", "a   b\tc")
    print(out)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["x", "1", "a b c"], _case_main))
