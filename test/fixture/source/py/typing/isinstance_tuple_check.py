class Cat:
    pass

class Dog:
    pass

def is_pet(x: object) -> bool:
    return isinstance(x, (Cat, Dog))

if __name__ == "__main__":
    c: Cat = Cat()
    d: Dog = Dog()
    print(is_pet(c))
    print(is_pet(d))
    print(is_pet(42))
