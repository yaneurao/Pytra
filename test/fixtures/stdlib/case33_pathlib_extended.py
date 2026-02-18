
from py_module.py_runtime import py_assert_stdout
from pathlib import Path


def main():
    root = Path("test/transpile/obj/pathlib_case32")
    root.mkdir(parents=True, exist_ok=True)

    child = root / "values.txt"
    child.write_text("42")

    print(child.exists())
    print(child.name)
    print(child.stem)
    print((child.parent / "values.txt").exists())
    print(child.read_text())


def _case_main() -> None:
    main()

if __name__ == "__main__":
    print(py_assert_stdout(['True', 'values.txt', 'values', 'True', '42'], _case_main))
