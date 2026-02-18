from pylib.assertions import py_assert_eq


class Base:
    def __init__(self) -> None:
        self.value: int = 1


class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.value += 1

    def get_value(self) -> int:
        return self.value


def _case_main() -> None:
    c: Child = Child()
    print(c.get_value())


if __name__ == "__main__":
    c: Child = Child()
    print(py_assert_eq(c.get_value(), 2, "super_init"))
