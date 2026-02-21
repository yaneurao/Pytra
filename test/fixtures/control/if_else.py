# This file contains test/implementation code for `test/fixtures/if_else.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def abs_like(n: int) -> int:
    if n < 0:
        return -n
    else:
        return n


def _case_main() -> None:
    print(abs_like(-12))

if __name__ == "__main__":
    print(py_assert_stdout(['12'], _case_main))
