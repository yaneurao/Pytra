# self_hosted parser signature test: class inline method `def ...: return ...` is accepted.


class Value:
    def __pow__(self, other: object) -> object:
        return self


if __name__ == "__main__":
    v: Value = Value()
    print(type(v).__name__)
