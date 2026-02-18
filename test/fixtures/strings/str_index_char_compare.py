def run_case() -> None:
    s: str = "ABC"
    i: int = 1
    ch: str = s[i]
    ok: bool = s[i] == "B"
    ok2: bool = s[0] != "B"
    print(ok and ok2 and ch == "B")


if __name__ == "__main__":
    run_case()
