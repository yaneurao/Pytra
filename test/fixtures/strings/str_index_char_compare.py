def run_case() -> None:
    s: str = "ABC"
    i: int = 1
    ch: byte = s[i]
    ok: bool = s[i] == "B"
    ok2: bool = s[0] != "B"
    print(ok and ok2 and ch == 66)


if __name__ == "__main__":
    run_case()
