# This file contains test/implementation code for `test/fixtures/inheritance.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Animal:
    def bark(self) -> str:
        return "animal bark"


class Dog(Animal):
    def bark(self) -> str:
        return "dog bark"


def _case_main() -> None:
    d: Animal = Dog()
    print(d.bark())

if __name__ == "__main__":
    print(py_assert_stdout(['dog bark'], _case_main))
