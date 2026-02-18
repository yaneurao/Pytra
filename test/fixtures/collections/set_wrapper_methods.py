def run_case() -> None:
    s: set[int] = {1, 2}
    s.discard(3)
    s.remove(1)

    ok_size: bool = len(s) == 1
    ok_has_2: bool = 2 in s
    ok_no_1: bool = not (1 in s)

    print(ok_size and ok_has_2 and ok_no_1)


if __name__ == "__main__":
    run_case()
