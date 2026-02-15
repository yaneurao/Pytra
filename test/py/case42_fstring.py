def make_msg_42(name: str, count: int) -> str:
    return f"{name}:42:{count}"


if __name__ == "__main__":
    print(make_msg_42("user", 7))
