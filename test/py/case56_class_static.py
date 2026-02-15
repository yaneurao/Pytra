class Counter56:
    total: int = 0

    def add(self, x: int) -> int:
        self.total = self.total + x
        return self.total


if __name__ == "__main__":
    c: Counter56 = Counter56()
    print(c.add(5))
