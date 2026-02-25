# This file contains test/implementation code for `test/fixtures/oop/inheritance_polymorphic_dispatch.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Animal:
    def bark(self) -> str:
        return "animal bark"


class Dog(Animal):
    def bark(self) -> str:
        return "dog bark"

class Chihuahua(Dog):
    def bark(self) -> str:
        return "chihuahua bark"


def _case_main() -> None:
    d: Animal = Chihuahua()
    print(d.bark())

if __name__ == "__main__":
    print(py_assert_stdout(['chihuahua bark'], _case_main))
