class Base41:
    def value(self) -> int:
        return 41


class Child41(Base41):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child41 = Child41()
    print(c.value2())
