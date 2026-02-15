class Base81:
    def value(self) -> int:
        return 81


class Child81(Base81):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child81 = Child81()
    print(c.value2())
