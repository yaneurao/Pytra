# This file contains test/implementation code for `test/fixtures/nested_call.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def inc(x: int) -> int:
    return x + 1


def twice(x: int) -> int:
    return inc(inc(x))


def _case_main() -> None:
    print(twice(10))

if __name__ == "__main__":
    print(py_assert_stdout(['12'], _case_main))
