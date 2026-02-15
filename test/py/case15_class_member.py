class Counter:
    value: int = 0

    def inc(self) -> int:
        self.value = self.value + 1
        return self.value


if __name__ == "__main__":
    c: Counter = Counter()
    print(c.inc())
