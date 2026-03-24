# self_hosted parser: tuple of list comprehensions.


def run_tuple_of_list_comp() -> None:
    n_layer: int = 2
    keys: list[list[int]] = [[] for _ in range(n_layer)]
    values: list[list[int]] = [[] for _ in range(n_layer)]
    print(len(keys), len(values))


if __name__ == "__main__":
    run_tuple_of_list_comp()
