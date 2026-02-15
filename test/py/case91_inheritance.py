class Base91:
    def value(self) -> int:
        return 91


class Child91(Base91):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child91 = Child91()
    print(c.value2())
