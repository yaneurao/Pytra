from pylib import sys
from pylib.assertions import py_assert_stdout


def main() -> None:
    old_argv = sys.argv
    old_path = sys.path
    sys.set_argv(["a", "b"])
    sys.set_path(["x"])
    print(isinstance(sys.argv, list))
    print(isinstance(sys.path, list))
    print(sys.argv[0])
    print(sys.path[0])
    sys.set_argv(old_argv)
    sys.set_path(old_path)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["True", "True", "a", "x"], _case_main))
