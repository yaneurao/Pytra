# This file contains test/implementation code for `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`.

from pytra.utils.assertions import py_assert_stdout


class Animal:
    def speak(self) -> str:
        return "animal"


class Dog(Animal):
    def speak(self) -> str:
        return "dog"


class LoudDog(Dog):
    def speak(self) -> str:
        return "loud-" + super().speak()


def call_via_animal(a: Animal) -> str:
    return a.speak()


def call_via_dog(d: Dog) -> str:
    return d.speak()


def _case_main() -> None:
    a: Animal = LoudDog()
    d: Dog = LoudDog()
    print(call_via_animal(a))
    print(call_via_dog(d))


if __name__ == "__main__":
    print(py_assert_stdout(["loud-dog", "loud-dog"], _case_main))
