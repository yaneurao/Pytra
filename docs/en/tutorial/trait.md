<a href="../../ja/tutorial/trait.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Traits (Interfaces)

This page explains how to use **traits** (interfaces) in Pytra. Traits let you attach multiple behavioral contracts to a type while keeping the single-inheritance constraint.

## What is a Trait?

You can only inherit from one class, but sometimes you want to require behaviors like "drawable" or "serializable" across multiple classes. Traits provide this mechanism.

They are equivalent to Rust's traits, Java's interfaces, and Swift's protocols.

## Defining a Trait

Define a trait with the `@trait` decorator on a class statement. The body contains only method signatures.

```python
@trait
class Drawable:
    def draw(self) -> None: ...
    def area(self) -> float: ...

@trait
class Serializable:
    def serialize(self) -> str: ...
```

A trait defines only the "contract" of methods. No implementation (method body) is written.

## Implementing a Trait

To have a class implement a trait, declare it with the `@implements` decorator.

```python
class Circle(Shape):
    @implements(Drawable, Serializable)

    radius: float

    def __init__(self, r: float) -> None:
        self.radius = r

    def draw(self) -> None:
        print("drawing circle with radius " + str(self.radius))

    def area(self) -> float:
        return 3.14 * self.radius * self.radius

    def serialize(self) -> str:
        return "circle:" + str(self.radius)
```

Key points:

- `Circle(Shape)` inherits from Shape (single inheritance as usual)
- `@implements(Drawable, Serializable)` implements 2 traits
- All methods declared in the traits must be implemented. Missing even one causes a compile error

## Accepting a Trait Type

You can use a trait type as a function parameter. Any class that implements the trait can be passed.

```python
def render(d: Drawable) -> None:
    d.draw()
    print("area: " + str(d.area()))

c: Circle = Circle(5.0)
render(c)  # OK: Circle implements Drawable
```

The conversion (upcast) from `Circle` to `Drawable` happens automatically. No explicit cast is needed.

## Implicit Conversion Rules

In Pytra, the following implicit type conversions (upcasts) are available. No explicit cast is needed.

| From | To | Condition |
|---|---|---|
| Subclass | Parent class | Inheritance relationship exists (`class Circle(Shape):`) |
| Concrete class | Trait type | Declared with `@implements` |

```python
class Shape:
    pass

@trait
class Drawable:
    def draw(self) -> None: ...

class Circle(Shape):
    @implements(Drawable)
    def draw(self) -> None: ...

c: Circle = Circle()

# Inheritance upcast: Circle → Shape
def process_shape(s: Shape) -> None: ...
process_shape(c)  # OK

# Trait upcast: Circle → Drawable
def render(d: Drawable) -> None: ...
render(c)  # OK

# NG: conversion to unrelated type
def bad(x: object) -> None: ...
bad(c)  # Calling methods on object is forbidden, so accepting as object is meaningless
```

All conversions are verified at compile time. Conversions that don't meet the conditions result in compile errors.

## Type Checking is at Compile Time

Whether a trait is implemented is verified at compile time. If you accept with a trait type, a type mismatch on the caller side results in a compile error.

```python
def render(d: Drawable) -> None:
    d.draw()  # OK: d is typed as Drawable

c: Circle = Circle(5.0)
render(c)  # OK: Circle implements Drawable

s: Square = Square()  # Square does not implement Drawable
render(s)  # Compile error: Square does not implement Drawable
```

There is no need to check "does this value implement the trait?" at runtime with `isinstance`. Specifying the trait in the type annotation guarantees safety at compile time.

## Multiple Classes Implementing the Same Trait

The value of traits is defining a common behavior across different classes.

```python
@trait
class Serializable:
    def serialize(self) -> str: ...

class Circle(Shape):
    @implements(Serializable)
    def serialize(self) -> str:
        return "circle:" + str(self.radius)

class Rectangle(Shape):
    @implements(Serializable)
    def serialize(self) -> str:
        return "rect:" + str(self.width) + "x" + str(self.height)

def save_all(items: list[Serializable]) -> None:
    for item in items:
        print(item.serialize())
```

`Circle` and `Rectangle` are different classes, but both implement `Serializable`, so they can be put in a `list[Serializable]` and handled uniformly.

## Trait Inheritance

Traits can inherit from other traits.

```python
@trait
class Printable:
    def to_string(self) -> str: ...

@trait
class DebugPrintable(Printable):
    def debug_string(self) -> str: ...
```

A class implementing `DebugPrintable` must implement both `to_string` and `debug_string`.

## Constraints

- Traits cannot have fields (data attributes)
- Traits cannot have method implementations (signatures only)
- Traits cannot be instantiated (`Drawable()` is an error)
- All methods of declared traits must be implemented, or a compile error occurs
- You cannot call trait methods on an `object` / `Any` typed variable. You also cannot pass `object` to a trait-typed parameter (`object` does not implement any trait). If you want to use a trait, declare the argument or variable with the trait type

```python
# NG: cannot call trait methods on object
def bad(x: object) -> None:
    x.draw()  # Compile error: method calls on object are forbidden

# NG: cannot pass object to a trait type either
def render(d: Drawable) -> None:
    d.draw()

x: object = Circle(5.0)
render(x)  # Compile error: object does not implement Drawable

# OK: if the variable has a known type, it can be passed
c: Circle = Circle(5.0)
render(c)  # OK
```

## Trait vs Inheritance: When to Use Which

| Situation | Use |
|---|---|
| "A is a kind of B" (is-a) | Class inheritance (`class Dog(Animal):`) |
| "A can do this behavior" (can-do) | Trait (`@implements(Drawable)`) |
| Want to share data (fields) | Class inheritance |
| Want to satisfy multiple contracts at once | Trait (multiple allowed) |

## Summary

| Goal | How to write |
|---|---|
| Define a trait | `@trait class A: def method(self) -> T: ...` |
| Implement a trait | Add `@implements(A, B)` to a class |
| Accept a trait type | `def f(x: A) -> None:` |
| Type checking | Verified automatically at compile time (no runtime isinstance needed) |

For detailed specifications, see:
- [Trait specification](../spec/spec-trait.md) — Mapping rules for each language, EAST representation, validation rules
