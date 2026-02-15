class Base31:
    def value(self) -> int:
        return 31


class Child31(Base31):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child31 = Child31()
    print(c.value2())
