import math


def main() -> None:
    print(math.fabs(math.tan(0.0)) < 1e-12)
    print(math.fabs(math.log(math.exp(1.0)) - 1.0) < 1e-12)
    print(int(math.log10(1000.0)))
    print(int(math.fabs(-3.5) * 10.0))
    print(int(math.ceil(2.1)))
    print(int(math.pow(2.0, 5.0)))


if __name__ == "__main__":
    main()
