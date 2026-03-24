# self_hosted parser: top-level for statement.


def run_top_level_for() -> int:
    xs: list[int] = [1, 2, 3]
    acc: int = 0
    for x in xs:
        acc = acc + x
    return acc


if __name__ == "__main__":
    print(run_top_level_for())
