# This file contains test/implementation code for `test/fixtures/oop/is_instance.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout

class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal):
    pass


def _case_main() -> None:
    cat = Cat()
    dog = Dog()
    print(isinstance(cat, Dog))
    print(isinstance(cat, Animal))
    print(isinstance(dog, Cat))
    print(isinstance(dog, Animal))

if __name__ == "__main__":
    print(py_assert_stdout(['False','True','False','True'], _case_main))
