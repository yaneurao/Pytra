# self_hosted parser: list concatenation with comprehension.


def run_list_concat_comp() -> None:
    BOS: int = 1
    uchars: list[str] = ["a", "b"]
    doc: str = "ab"
    tokens: list[int] = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
    print(tokens)


if __name__ == "__main__":
    run_list_concat_comp()
