# Regression: preserve method receiver for str.join in selfhost direct transpile.

from pytra.utils.assertions import py_assert_stdout


def join_words() -> str:
    sep: str = ","
    items: list[str] = ["a", "b", "c"]
    return sep.join(items)


def _case_main() -> None:
    print(join_words())


if __name__ == "__main__":
    print(py_assert_stdout(["a,b,c"], _case_main))
