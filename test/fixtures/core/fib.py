# This file contains test/implementation code for `test/fixtures/fib.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def fib(n: int) -> int:
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


def _case_main() -> None:
    print(fib(10))

if __name__ == "__main__":
    print(py_assert_stdout(['55'], _case_main))
