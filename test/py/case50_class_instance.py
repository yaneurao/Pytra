class Box50:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed = self.seed + 1
        return self.seed


if __name__ == "__main__":
    b: Box50 = Box50(3)
    print(b.next())
