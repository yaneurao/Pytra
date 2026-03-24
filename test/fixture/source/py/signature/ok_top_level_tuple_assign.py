# self_hosted parser: top-level tuple parallel assignment.


def run_tuple_assign() -> None:
    a: int = 1
    b: int = 2
    a, b = b, a
    print(a, b)


if __name__ == "__main__":
    run_tuple_assign()
