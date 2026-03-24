# self_hosted parser: top-level if with import in block.


def run_top_level_if() -> int:
    x: int = 1
    if x > 0:
        x = x + 1
    return x


if __name__ == "__main__":
    print(run_top_level_if())
