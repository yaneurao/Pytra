def linear(x, w):
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]

