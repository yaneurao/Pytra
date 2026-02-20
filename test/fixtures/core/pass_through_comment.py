"""Pytra comment passthrough (`# Pytra::cpp` / `# Pytra::pass`) の最小ケース。"""

from pytra.utils.assertions import py_assert_true


def line_injection(x: int) -> int:
    # Pytra::cpp int injected = x;
    # Pytra::cpp injected += 1;
    return x + 1


def block_injection(x: int) -> int:
    # Pytra::pass begin
    # int temp = x;
    # temp += 1;
    # Pytra::pass end
    return x + 1


def main() -> None:
    ok: bool = line_injection(2) == 3 and block_injection(2) == 3
    print(ok)
    py_assert_true(ok, "pass_through_comment")


if __name__ == "__main__":
    main()
