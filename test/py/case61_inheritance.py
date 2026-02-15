class Base61:
    def value(self) -> int:
        return 61


class Child61(Base61):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child61 = Child61()
    print(c.value2())
