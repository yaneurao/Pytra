def decorate(name: str) -> str:
    prefix: str = "[USER] "
    message: str = prefix + name
    return message + "!"


if __name__ == "__main__":
    print(decorate("Alice"))
