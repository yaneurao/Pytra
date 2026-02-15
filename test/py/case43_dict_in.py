def has_key_43(k: str) -> bool:
    d: dict[str, int] = {"a": 1, "b": 2}
    if k in d:
        return True
    else:
        return False


if __name__ == "__main__":
    print(has_key_43("a"))
