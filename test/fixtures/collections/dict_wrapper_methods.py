def run_case() -> None:
    d: dict[str, int] = {"a": 1, "b": 2}

    ok_get_default: bool = d.get("x", 99) == 99
    ok_get_exist: bool = d.get("a", 0) == 1

    ks: list[str] = d.keys()
    vs: list[int] = d.values()

    has_a: bool = "a" in ks
    has_2: bool = 2 in vs

    print(ok_get_default and ok_get_exist and has_a and has_2)


if __name__ == "__main__":
    run_case()
