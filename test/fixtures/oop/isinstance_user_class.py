class Base:
    pass

class Child(Base):
    pass

def check(x: object) -> bool:
    return isinstance(x, Base)

if __name__ == "__main__":
    b: Base = Base()
    c: Child = Child()
    print(check(b))
    print(check(c))
    print(isinstance(c, Child))
