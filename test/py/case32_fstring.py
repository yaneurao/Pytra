def make_msg_32(name: str, count: int) -> str:
    return f"{name}:32:{count}"


if __name__ == "__main__":
    print(make_msg_32("user", 7))
