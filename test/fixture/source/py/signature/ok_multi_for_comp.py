# self_hosted parser: list comprehension with multiple for clauses.


def run_multi_for_comp() -> None:
    rows: list[list[int]] = [[1, 2], [3]]
    flat: list[int] = [x for row in rows for x in row]
    print(flat)


if __name__ == "__main__":
    run_multi_for_comp()
