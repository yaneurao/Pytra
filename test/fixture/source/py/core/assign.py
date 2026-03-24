# This file contains test/implementation code for `test/fixtures/assign.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def square_plus_one(n: int) -> int:
    result = n * n
    result += 1
    return result


def _case_main() -> None:
    print(square_plus_one(5))

if __name__ == "__main__":
    print(py_assert_stdout(['26'], _case_main))
