class Counter66:
    total: int = 0

    def add(self, x: int) -> int:
        self.total = self.total + x
        return self.total


if __name__ == "__main__":
    c: Counter66 = Counter66()
    print(c.add(5))
