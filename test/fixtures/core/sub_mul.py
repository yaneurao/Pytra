# This file contains test/implementation code for `test/fixtures/sub_mul.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def calc(x: int, y: int) -> int:
    return (x - y) * 2

def div_calc(x: int, y: int) -> float:
    return x / y


def _case_main() -> None:
    print(calc(9, 4))
    print(div_calc(9, 4))

if __name__ == "__main__":
    print(py_assert_stdout(['10', '2.25'], _case_main))
