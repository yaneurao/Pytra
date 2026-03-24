# This file contains test/implementation code for `test/fixtures/class_instance.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Box100:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed += 1
        return self.seed


def _case_main() -> None:
    b: Box100 = Box100(3)
    print(b.next())

if __name__ == "__main__":
    print(py_assert_stdout(['4'], _case_main))
