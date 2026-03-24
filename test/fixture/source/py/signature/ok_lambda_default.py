# self_hosted parser: lambda with default argument.


def run_lambda_default() -> None:
    matrix = lambda nout, nin, std=0.08: nout + nin * std
    print(matrix(1, 2))
    print(matrix(1, 2, 0.5))


if __name__ == "__main__":
    run_lambda_default()
