class Base:
    def speak(self) -> str:
        return "base"

class Child(Base):
    def speak(self) -> str:
        return "child"

if __name__ == "__main__":
    b: Base = Base()
    c: Child = Child()
    print(b.speak())
    print(c.speak())
    print(isinstance(c, Base))
