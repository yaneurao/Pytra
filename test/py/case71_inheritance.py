class Base71:
    def value(self) -> int:
        return 71


class Child71(Base71):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child71 = Child71()
    print(c.value2())
