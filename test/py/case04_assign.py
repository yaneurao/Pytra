def square_plus_one(n: int) -> int:
    result: int = n * n
    result = result + 1
    return result


if __name__ == "__main__":
    print(square_plus_one(5))
