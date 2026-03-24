# This file contains test/implementation code for `test/fixtures/class.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Multiplier:
    def mul(self, x: int, y: int) -> int:
        return x * y


def _case_main() -> None:
    m: Multiplier = Multiplier()
    print(m.mul(6, 7))

if __name__ == "__main__":
    print(py_assert_stdout(['42'], _case_main))
