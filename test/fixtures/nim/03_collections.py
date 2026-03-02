
def list_test() -> list[int]:
    items = [1, 2, 3]
    items.append(4)
    return items

def dict_test() -> dict[str, int]:
    d = {"a": 1, "b": 2}
    return d

def tuple_test() -> tuple[int, int]:
    return (10, 20)

if __name__ == "__main__":
    print(list_test())
    print(dict_test())
    print(tuple_test())
