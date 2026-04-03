<a href="../../ja/spec/spec-trait.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

# Trait Specification (Pure Interface and Multiple Implementation)

Last updated: 2026-03-27
Status: Draft

## 1. Purpose

- Provide a mechanism for attaching multiple behavioral contracts to a type while preserving Python's single-inheritance constraint.
- Map to each target language's native interface, trait, or protocol construct.
- Realize `isinstance` checks on a separate `trait_id` axis that is independent of `type_id` (interval-based single-inheritance lookup).

## 2. Non-goals

- Default implementations (giving a trait a method body). Traits are pure interfaces.
- Structural subtyping. Trait implementation is nominal (explicit declaration required).
- First-class trait object support (a dynamic dispatch container equivalent to `Box<dyn T>`).

## 3. Syntax

### 3.1 Trait declaration

Declared with a `class` statement annotated with `@trait`. The body contains only method signatures (`...` body).

```python
@trait
class Drawable:
    def draw(self) -> None: ...
    def area(self) -> float: ...

@trait
class Serializable:
    def serialize(self) -> str: ...
```

Constraints:

- A trait cannot be instantiated.
- A trait cannot have fields (data attributes).
- A trait may inherit from another trait (trait inheritance). In `@trait class A(B):`, B must also be `@trait`.
- A trait cannot inherit from a class.
- If a method has a body other than `...`, the compiler halts fail-closed with `unsupported_syntax`.

### 3.2 Trait implementation

Use the `@implements` decorator to declare which traits a class implements. This is independent of single inheritance.

```python
class Circle(Shape):
    @implements(Drawable, Serializable)

    def draw(self) -> None:
        print("drawing circle")

    def area(self) -> float:
        return 3.14 * self.radius * self.radius

    def serialize(self) -> str:
        return "circle:" + str(self.radius)
```

Constraints:

- Every method of every trait listed in `@implements` must be implemented. Missing implementations halt fail-closed with `semantic_conflict`.
- A single class may implement multiple traits.
- `@implements` is written exactly once, directly under the `class` statement.

### 3.3 Trait types as arguments

Trait types may be used as type annotations for function parameters or variables.

```python
def render(d: Drawable) -> None:
    d.draw()

c: Circle = Circle()
render(c)  # implicit upcast from Circle to Drawable
```

## 4. Relationship to the Type System

### 4.1 Separation from type_id

- Traits have no `type_id` (they cannot be instantiated).
- Traits carry no information at runtime. Verification is compile-time only.
- The single-inheritance `type_id` tree is not affected by traits.

### 4.2 Trait upcast

An instance of class X that declares `@implements(A)` may be used implicitly as type `A`.

- The resolve stage verifies at compile time that X implements A.
- If verification passes, no explicit cast is needed.
- EAST3 retains the fact that this is a trait upcast as metadata.
- The emitter maps this to each language's implicit upcast (most languages require no additional code).

### 4.3 isinstance

Trait isinstance checks are verified statically by the resolver at compile time. No runtime judgment code is generated.

```python
def f(x: Drawable) -> None:
    x.draw()  # OK: x is typed as Drawable at compile time

c: Circle = Circle()
# isinstance(c, Drawable) is evaluated as True statically by the resolver at compile time.
# Because Pytra forbids method calls on object/Any,
# there is no situation that requires a runtime trait check.
```

## 5. EAST Representation

### 5.1 Trait declaration

Attach `meta.trait_v1` to a `ClassDef`.

```json
{
  "kind": "ClassDef",
  "name": "Drawable",
  "decorators": ["trait"],
  "meta": {
    "trait_v1": {
      "schema_version": 1,
      "methods": [
        {"name": "draw", "args": ["self"], "return_type": "None"},
        {"name": "area", "args": ["self"], "return_type": "float64"}
      ],
      "extends_traits": []
    }
  }
}
```

### 5.2 Trait implementation

Attach `meta.implements_v1` to a `ClassDef`.

```json
{
  "kind": "ClassDef",
  "name": "Circle",
  "bases": ["Shape"],
  "decorators": ["implements(Drawable, Serializable)"],
  "meta": {
    "implements_v1": {
      "schema_version": 1,
      "traits": ["Drawable", "Serializable"]
    }
  }
}
```

### 5.3 Trait method marker

Among the methods of a class that implements a trait, those that implement a trait method receive `meta.trait_impl_v1` on their `FunctionDef`.

```json
{
  "kind": "FunctionDef",
  "name": "draw",
  "meta": {
    "trait_impl_v1": {
      "schema_version": 1,
      "trait_name": "Drawable",
      "method_name": "draw"
    }
  }
}
```

- During the resolve stage, the methods of traits listed in `@implements` are matched against the class's methods, and matching methods receive `trait_impl_v1`.
- When a single method simultaneously implements methods from multiple traits (when the same method name appears in multiple traits), `trait_impl_v1` is stored as a list.
- Methods without `trait_impl_v1` are treated as methods specific to that class.

The emitter uses this marker to produce language-specific output:

| Language | Methods with `trait_impl_v1` |
|---|---|
| Rust | placed inside an `impl Drawable for Circle { fn draw(&self) { ... } }` block |
| Java / Kotlin | annotated with `@Override` |
| C++ | given the `override` keyword |
| Swift | treated as protocol conformance methods |
| Go / TS / C# | no additional modifier (the language resolves this automatically) |

### 5.4 Trait upcast

Locations where the resolve stage has already verified a trait upcast are treated as implicit casts, requiring no additional judgment from the emitter.

## 6. Mapping to Each Language

### 6.1 Trait declaration

| Language | Mapping |
|---|---|
| Java | `interface Drawable { void draw(); float area(); }` |
| C# | `interface IDrawable { void Draw(); float Area(); }` |
| Kotlin | `interface Drawable { fun draw(); fun area(): Double }` |
| Swift | `protocol Drawable { func draw(); func area() -> Double }` |
| Go | `type Drawable interface { Draw(); Area() float64 }` |
| Rust | `trait Drawable { fn draw(&self); fn area(&self) -> f64; }` |
| C++ | `class Drawable { public: virtual void draw() = 0; virtual double area() = 0; virtual ~Drawable() = default; };` (trait-to-trait inheritance uses `virtual` inheritance) |
| TS | `interface Drawable { draw(): void; area(): number; }` |

### 6.2 Trait implementation

| Language | Mapping |
|---|---|
| Java | `class Circle extends Shape implements Drawable, Serializable` |
| C# | `class Circle : Shape, IDrawable, ISerializable` |
| Kotlin | `class Circle : Shape(), Drawable, Serializable` |
| Swift | `class Circle: Shape, Drawable, Serializable` |
| Go | Structural (no explicit declaration needed; satisfying the methods is sufficient) |
| Rust | `impl Drawable for Circle { ... }` + `impl Serializable for Circle { ... }` |
| C++ | `class Circle : public Shape, virtual public Drawable, virtual public Serializable` (traits use `virtual` inheritance) |
| TS | `class Circle extends Shape implements Drawable, Serializable` |

### 6.3 Trait upcast (X → A)

| Language | Mapping |
|---|---|
| Java / C# / Kotlin / Swift / TS | Implicit (guaranteed by the compiler) |
| Go | Implicit (`var d Drawable = c`) |
| Rust | `&c as &dyn Drawable` or `Box<dyn Drawable>` |
| C++ | Implicit conversion via the conversion constructor of `Object<T>` (see §6.4) |

### 6.4 C++ `Object<T>` trait upcast support

In C++, traits are multiply inherited as pure virtual classes, and a templated conversion constructor is added to `Object<T>`.

```cpp
template<typename T>
class Object {
    T* ptr;
    RefCount* rc;
public:
    // Allow implicit conversion when U* is convertible to T*
    template<typename U,
             typename = std::enable_if_t<std::is_convertible_v<U*, T*>>>
    Object(const Object<U>& other) : ptr(other.ptr), rc(other.rc) {
        rc->inc();
    }
};
```

This makes `Object<Circle>` → `Object<Drawable>` an implicit conversion.

### 6.5 C++ diamond problem with trait-to-trait inheritance

When a trait inherits from another trait, C++ encounters the diamond problem.

```python
@trait
class Printable:
    def to_string(self) -> str: ...

@trait
class DebugPrintable(Printable):
    def debug_string(self) -> str: ...

@trait
class Loggable(Printable):
    def log(self) -> None: ...

class MyClass(Base):
    @implements(DebugPrintable, Loggable)  # Printable arrives via two paths
```

The C++ emitter resolves this with **virtual inheritance**:

```cpp
class Printable { public: virtual std::string to_string() = 0; virtual ~Printable() = default; };
class DebugPrintable : virtual public Printable { public: virtual std::string debug_string() = 0; };
class Loggable : virtual public Printable { public: virtual void log() = 0; };

class MyClass : public Base, virtual public DebugPrintable, virtual public Loggable {
    // Only one Printable (via virtual inheritance)
    std::string to_string() override { ... }
    std::string debug_string() override { ... }
    void log() override { ... }
};
```

Rules:

- All trait-to-trait inheritance is emitted with `virtual public`.
- Class-to-trait implements is also emitted with `virtual public`.
- The overhead of virtual inheritance is minimal because traits are pure interfaces (no fields, no implementation).
- Trait method implementations receive the `override` keyword (see `meta.trait_impl_v1`).

Other languages (Java, C#, Kotlin, Swift, Go, Rust, TS) natively support multiple interface implementation, so the diamond problem does not arise.

## 7. isinstance and Traits

Trait isinstance checks are **verified statically by the resolver at compile time only**; no runtime judgment is needed.

Reasons:

- Pytra forbids method calls on `object`/`Any`.
- When a parameter is typed as a trait, its type is fixed at compile time. There is no situation where runtime must ask "does this value implement the trait?"
- `isinstance(x, Drawable)` is resolved at compile time by the resolver, which statically checks whether the type of `x` has `@implements` for `Drawable` and performs narrowing. No runtime judgment code is generated.

Prohibited:

- Do not give the runtime trait_id, trait_bits, or a trait bitset.
- Do not store trait information in ControlBlock or TypeInfo.
- Do not have the linker generate a trait_id table.
- Traits are a type-system (compile-time) concept, not a runtime dispatch concept.

## 8. Verification (Resolve Stage)

The resolve stage statically verifies the following:

1. Every method of every trait listed in `@implements` is implemented in the class.
2. Method signatures (parameter types and return types) match the trait declaration.
3. Values passed to a function whose parameter is a trait type actually implement that trait.
4. No trait declaration contains a method body (anything other than `...`).

Verification failures halt fail-closed with `semantic_conflict`.

## 9. Future Extensions (Out of Scope)

- Default implementations: deferred from v1 because they require automatic delegation-method generation in Go and would sharply increase emitter complexity.
- Trait bounds (`@template("T: Comparable")`): integration with `@template`. Will be addressed after the trait foundation stabilizes.
- Associated types: equivalent to Rust's associated types. To be considered when demand arises.

## 10. Related

- `docs/ja/spec/spec-type_id.md` — definition of `type_id` / `trait_id`
- `docs/ja/spec/spec-east.md` — EAST node specification
- `docs/ja/spec/spec-emitter-guide.md` — emitter mapping conventions
