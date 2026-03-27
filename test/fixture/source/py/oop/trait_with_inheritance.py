# Test: trait + class inheritance combination.
# Circle inherits from Shape (single inheritance) and implements
# Drawable + Serializable (trait). Tests upcast to both parent class
# and trait types.

from pytra.utils.assertions import py_assert_stdout


class _IdentityDecorator:
    def __call__(self, cls: object) -> object:
        return cls


class _ImplementsFactory:
    def __call__(self, *_traits: object) -> object:
        return _IdentityDecorator()


trait = _IdentityDecorator()
implements = _ImplementsFactory()


class Shape:
    def kind(self) -> str:
        return "shape"


@trait
class Drawable:
    def draw(self) -> str: ...


@trait
class Serializable:
    def serialize(self) -> str: ...


@implements(Drawable, Serializable)
class Circle(Shape):
    def __init__(self, r: int) -> None:
        self.radius: int = r

    def draw(self) -> str:
        return "circle r=" + str(self.radius)

    def serialize(self) -> str:
        return "circle:" + str(self.radius)


@implements(Drawable)
class Square(Shape):
    def __init__(self, s: int) -> None:
        self.side: int = s

    def draw(self) -> str:
        return "square s=" + str(self.side)


# Upcast to parent class
def describe_shape(s: Shape) -> str:
    return s.kind()


# Upcast to trait
def render(d: Drawable) -> str:
    return d.draw()


# Upcast to another trait
def save(s: Serializable) -> str:
    return s.serialize()


def _case_main() -> None:
    c: Circle = Circle(5)
    sq: Square = Square(3)

    # Inheritance upcast: Circle/Square -> Shape
    print(describe_shape(c))
    print(describe_shape(sq))

    # Trait upcast: Circle/Square -> Drawable
    print(render(c))
    print(render(sq))

    # Trait upcast: Circle -> Serializable
    print(save(c))

    # Direct method call
    print(c.kind())
    print(c.radius)


if __name__ == "__main__":
    print(py_assert_stdout([
        "shape", "shape",
        "circle r=5", "square s=3",
        "circle:5",
        "shape", "5",
    ], _case_main))
