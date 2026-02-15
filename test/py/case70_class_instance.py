class Box70:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed = self.seed + 1
        return self.seed


if __name__ == "__main__":
    b: Box70 = Box70(3)
    print(b.next())
