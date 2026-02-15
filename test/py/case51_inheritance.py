class Base51:
    def value(self) -> int:
        return 51


class Child51(Base51):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child51 = Child51()
    print(c.value2())
