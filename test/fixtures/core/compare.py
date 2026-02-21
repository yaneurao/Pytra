# This file contains test/implementation code for `test/fixtures/compare.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def is_large(n: int) -> bool:
    if n >= 10:
        return True
    else:
        return False


def _case_main() -> None:
    print(is_large(11))

if __name__ == "__main__":
    print(py_assert_stdout(['True'], _case_main))
