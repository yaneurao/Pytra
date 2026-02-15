class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y: int = y

    def total(self) -> int:
        return self.x + self.y


if __name__ == "__main__":
    p: Point = Point(2, 5)
    print(p.total())
