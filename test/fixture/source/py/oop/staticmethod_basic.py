class MathUtil:
    @staticmethod
    def double(x: int) -> int:
        return x * 2

    @staticmethod
    def triple(x: int) -> int:
        return x * 3

if __name__ == "__main__":
    print(MathUtil.double(5))
    print(MathUtil.triple(4))
