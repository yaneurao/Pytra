def make_msg_22(name: str, count: int) -> str:
    return f"{name}:22:{count}"


if __name__ == "__main__":
    print(make_msg_22("user", 7))
