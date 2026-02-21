# This file contains test/implementation code for `test/fixtures/float.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def half(x: float) -> float:
    return x / 2.0


def _case_main() -> None:
    print(half(5.0))

if __name__ == "__main__":
    print(py_assert_stdout(['2.5'], _case_main))
