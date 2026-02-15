class Base21:
    def value(self) -> int:
        return 21


class Child21(Base21):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child21 = Child21()
    print(c.value2())
