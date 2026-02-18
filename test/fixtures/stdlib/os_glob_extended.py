from pylib import glob, os
from pylib.assertions import py_assert_stdout


def main() -> None:
    joined = os.path.join("alpha", "beta.txt")
    root, ext = os.path.splitext(joined)
    print(os.path.basename(joined))
    print(root)
    print(ext)
    print(os.path.dirname(joined))
    print(os.path.exists("test/fixtures"))
    print(len(glob.glob("test/fixtures/core/*.py")) > 0)


def _case_main() -> None:
    main()


if __name__ == "__main__":
    print(py_assert_stdout(["beta.txt", "alpha/beta", ".txt", "alpha", "True", "True"], _case_main))
