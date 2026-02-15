def make_msg_92(name: str, count: int) -> str:
    return f"{name}:92:{count}"


if __name__ == "__main__":
    print(make_msg_92("user", 7))
