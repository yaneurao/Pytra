# This file contains test/implementation code for `test/fixtures/negative_index.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def last_item_25() -> int:
    stack: list[int] = [10, 20, 30, 40]
    return stack[-1]


def _case_main() -> None:
    print(last_item_25())

if __name__ == "__main__":
    print(py_assert_stdout(['40'], _case_main))
