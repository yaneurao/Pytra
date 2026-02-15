class Multiplier:
    def mul(self, x: int, y: int) -> int:
        return x * y


if __name__ == "__main__":
    m: Multiplier = Multiplier()
    print(m.mul(6, 7))
