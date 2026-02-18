def run_case() -> None:
    s: str = "ABC"
    out: str = ""
    count: int = 0
    for c in s:
        out += c
        count += 1
    print(out == "ABC" and count == 3)


if __name__ == "__main__":
    run_case()
