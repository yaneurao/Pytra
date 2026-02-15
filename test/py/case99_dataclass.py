from dataclasses import dataclass


@dataclass
class Point99:
    x: int
    y: int = 10

    def total(self) -> int:
        return self.x + self.y


if __name__ == "__main__":
    p: Point99 = Point99(3)
    print(p.total())
