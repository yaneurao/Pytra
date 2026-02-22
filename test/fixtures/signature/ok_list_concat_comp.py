BOS: int = 1
uchars: list[str] = ["a", "b"]
doc: str = "ab"
tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]

