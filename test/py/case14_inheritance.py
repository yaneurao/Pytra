class Animal:
    def sound(self) -> str:
        return "generic"


class Dog(Animal):
    def bark(self) -> str:
        return self.sound() + "-bark"


if __name__ == "__main__":
    d: Dog = Dog()
    print(d.bark())
