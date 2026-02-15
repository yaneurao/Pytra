def make_msg_82(name: str, count: int) -> str:
    return f"{name}:82:{count}"


if __name__ == "__main__":
    print(make_msg_82("user", 7))
