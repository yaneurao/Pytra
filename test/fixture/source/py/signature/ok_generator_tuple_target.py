def linear(x: list[float], w: list[list[float]]) -> list[float]:
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]


if __name__ == "__main__":
    result: list[float] = linear([1.0, 2.0], [[3.0, 4.0], [5.0, 6.0]])
    print(result)
