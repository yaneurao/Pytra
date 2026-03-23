def greet(name: str, greeting: str = "Hello") -> str:
    return greeting + " " + name

def add(a: int, b: int = 10) -> int:
    return a + b

if __name__ == "__main__":
    print(greet("world"))
    print(greet("world", "Hi"))
    print(add(5))
    print(add(5, 20))
