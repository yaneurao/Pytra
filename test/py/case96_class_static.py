class Counter96:
    total: int = 0

    def add(self, x: int) -> int:
        self.total = self.total + x
        return self.total


if __name__ == "__main__":
    c: Counter96 = Counter96()
    print(c.add(5))
