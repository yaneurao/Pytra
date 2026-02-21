# This file contains test/implementation code for `test/fixtures/not.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def invert(flag: bool) -> bool:
    if not flag:
        return True
    else:
        return False


def _case_main() -> None:
    print(invert(False))

if __name__ == "__main__":
    print(py_assert_stdout(['True'], _case_main))
