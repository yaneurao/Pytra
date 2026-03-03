def _case_main() -> None:
    token_tags: dict[str, int] = {
        "+": 1,
        "=": 7,
    }
    print(token_tags.get("=", 0))


if __name__ == "__main__":
    _case_main()
