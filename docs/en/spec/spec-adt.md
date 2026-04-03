<a href="../../ja/spec/spec-adt.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

# ADT (Algebraic Data Type) Specification

This document defines the policy for translating union types in Pytra into each target language.

## 1. Background

When translating Python union types (`int | str`, `str | None`, etc.) into statically typed languages, the previous approach degraded all of them to C++'s `object` implementation (`{type_id, rc<RcObject>}`). This caused:

- A large number of boxing / unboxing nodes to be generated
- Auxiliary mechanisms such as `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT` to be required
- The emitter to break down easily at `object` boundaries

However, most languages have union / enum / variant / sealed class constructs, making degradation to `object` unnecessary.

## 2. Policy

**Use the most appropriate representation for union types in each language. Do not unify all languages under `object`.**

## 3. Per-Language Translation Table

### 3.1 Languages with native tagged union / enum

| Language | Translation target | isinstance equivalent |
|---|---|---|
| Rust | `enum` | `if let Enum::Variant(x) = v` / `match` |
| Swift | `enum` with associated values | `if case let .variant(x) = v` |
| Kotlin | `sealed class` | `when (x) { is Type -> ... }` |
| Scala | `sealed trait` + `case class` | `match { case x: Type => ... }` |
| Nim | object variants | `case x.kind` |
| Zig | `union(enum)` | `switch (v)` |

In these languages, `int | str` is translated directly into an enum / variant. Degradation to `object` is not necessary.

Example (Rust):
```rust
enum IntOrStr {
    Int(i64),
    Str(String),
}

fn process(x: IntOrStr) {
    match x {
        IntOrStr::Int(n) => println!("{}", n),
        IntOrStr::Str(s) => println!("{}", s),
    }
}
```

### 3.2 Languages with variant types

| Language | Translation target | isinstance equivalent |
|---|---|---|
| C++ | `std::variant<T1, T2, ...>` (non-recursive), `struct { variant<...> }` (recursive) | `std::holds_alternative<T>(v)` / `std::visit` |

In C++, the representation differs between non-recursive and recursive cases:

- **Non-recursive** (`int | str`, `str | bool | None`): Use `std::variant` directly via a `using` type alias. `T | None` (two-type unions) is mapped to `OptionalType` as `std::optional<T>` (see §5.2). When `None` is mixed into a union of three or more types, the monostate approach (`std::variant<..., std::monostate>`) is also allowed (see [spec-emitter-guide.md §12.4](./spec-emitter-guide.md)).
- **Recursive** (types like `JsonVal` that contain themselves): Wrap in a `struct`. The right-hand side of a `using` declaration must be a complete type at the time of definition, so forward references are not possible; a `struct`, however, introduces the type name at the point of declaration, with member definitions only needing to be resolved before the closing brace. Recursive variant members are wrapped in `shared_ptr` to combine RC management with forward reference capability.

### C++ variant RC Management Rules

Whether each constituent of a variant is held as `T` or `std::shared_ptr<T>` depends on whether it is shared upon assignment in Python (mutable reference semantics):

| Union constituent | Type stored in variant | Reason |
|---|---|---|
| POD (`int`, `float`, `bool`) | `int64_t`, `double`, `bool` | Value type. Copying is fine. |
| `str` | `std::string` | Immutable. Copying is fine. |
| `None` (as part of `T \| None`) | Represented via `std::optional`, or `std::monostate` (for unions of 3+ types) | See §5.2 and [spec-emitter-guide.md §12.4](./spec-emitter-guide.md) |
| value class (`class_storage_hint: "value"`) | `T` | Value type. Copying is fine. |
| ref class (`class_storage_hint: "ref"`) | `std::shared_ptr<T>` | Shared in Python. RC is required. |
| `list[T]`, `dict[K,V]`, `set[T]` | `std::shared_ptr<container<...>>` | Mutable and shared in Python. |
| Recursive reference | `std::shared_ptr<T>` | Forward reference + RC |

EAST3 fields used to determine this:
- `class_storage_hint`: `"ref"` → `shared_ptr`; `"value"` → use as-is
- Container types (`list`, `dict`, `set`): always `shared_ptr` (Python's mutable containers have reference semantics)
- POD / `str` / `None`: use as-is

Examples:
```cpp
// int | MyClass (MyClass is a ref class)
using IntOrMyClass = std::variant<int64_t, std::shared_ptr<MyClass>>;

// str | list[int]
using StrOrList = std::variant<std::string, std::shared_ptr<std::vector<int64_t>>>;

// int | str | None — monostate approach (current emitter)
using IntOrStrOrNone = std::variant<int64_t, std::string, std::monostate>;
// or optional+variant approach: std::optional<std::variant<int64_t, std::string>>
```

Example (C++, non-recursive):
```cpp
using IntOrStr = std::variant<int64_t, std::string>;

void process(IntOrStr x) {
    if (std::holds_alternative<int64_t>(x)) {
        std::cout << std::get<int64_t>(x) << std::endl;
    } else {
        std::cout << std::get<std::string>(x) << std::endl;
    }
}
```

Example (C++, recursive — JsonVal):
```cpp
struct JsonVal {
    struct Null {};
    std::variant<
        int64_t,
        double,
        bool,
        std::string,
        Null,
        std::shared_ptr<std::vector<JsonVal>>,
        std::shared_ptr<std::map<std::string, JsonVal>>
    > value;
};
```

### 3.3 Languages with sealed class / abstract record

| Language | Translation target | isinstance equivalent |
|---|---|---|
| C# | abstract record / sealed class | `x is Type t` / `switch (x)` |
| Java | sealed class (Java 17+) | `x instanceof Type t` (Java 16+) |
| Dart | sealed class (Dart 3+) | `switch (x) { case Type() => ... }` |

### 3.4 Languages with native union types

| Language | Translation target | isinstance equivalent |
|---|---|---|
| TypeScript | `T1 \| T2` as-is | `typeof x === "..."` / discriminated union |
| JavaScript | No type annotations (dynamically typed by nature) | `typeof x` |

TypeScript can emit Python unions directly. No additional structures are needed.

### 3.5 Dynamically typed languages

| Language | Translation target | isinstance equivalent |
|---|---|---|
| Ruby | As-is (all variables are objects) | `x.is_a?(Type)` |
| Lua | As-is | `type(x)` |
| PHP | union type hint (PHP 8+) | `$x instanceof Type` |
| PowerShell | As-is | `-is [Type]` |
| Julia | `Union{T1, T2}` | `isa(x, Type)` |

In dynamically typed languages, all variables are already equivalent to `object`, so no special handling is needed when translating unions.

### 3.6 Languages with `any` + GC

| Language | Translation target | isinstance equivalent |
|---|---|---|
| Go | `any` (= `interface{}`) | `switch v := x.(type)` |

Go has no tagged union / enum, but `any` + GC maps directly to Python's `object` semantics. Method calls are made by first narrowing to a concrete type via type assertion. The isinstance narrowing + Unbox nodes in EAST3 represent this pattern.

### 3.7 Fallback for languages with neither ADT nor GC (reserved)

> All current target languages have one of: tagged union / enum / variant / sealed class / `any`. There are no languages this fallback currently applies to. It is retained as a reserve for any future statically typed language that lacks ADT support.

For statically typed languages without tagged unions and without GC, use a struct + tag representation:

```
struct IntOrStr {
    tag: enum { Int, Str },
    int_val: i64,
    str_val: str,
}
```

This wastes memory because all fields are present, but this is an inherent constraint of languages that do not support ADT, and is accepted. isinstance simply compares the tag field.

## 4. Handling Recursive Types

Recursive ADTs — types that contain themselves, like `JsonVal` — require pointers in some languages:

| Language | Handling of recursive types |
|---|---|
| Rust | `enum JsonVal { Arr(Vec<Box<JsonVal>>), ... }` — use Box for indirection |
| C++ | `struct JsonVal { std::variant<..., rc<std::vector<JsonVal>>> value; }` — wrap in struct, use rc for indirection on recursive variant members. `using` cannot forward-reference, but `struct` introduces the type name at declaration, making this possible. |
| Zig | `*JsonVal` for pointer indirection + custom RC or arena allocator |
| Go | No issue with `any` (GC-managed) |
| Swift | Explicitly use `indirect enum` |
| TS | Can be written directly (`type JsonVal = number \| JsonVal[]`) |
| C#/Java/Kotlin/Scala/Dart | Reference types, so recursion works naturally |

Non-recursive unions (`int | str`, `str | None`) pose no issues in any language.

**Even for recursive types, degradation to `object` is prohibited.** Express them as ADTs using each language's pointer / RC / GC mechanisms.

## 4.1 Shared References in ref classes (RC Management)

When a union / ADT contains ref class members or mutable containers, RC (reference counting) is required to preserve Python's reference-sharing semantics. Each language's approach:

| Language | Shared reference mechanism | Approach |
|---|---|---|
| C++ | `std::shared_ptr<T>` | Standard library |
| Rust | `Rc<T>` / `Arc<T>` | Standard library |
| Swift | ARC | Built into the language (automatic reference counting) |
| Nim | ARC or GC | Built into the language (selectable) |
| Zig | `SharedPtr(T)` | **Custom implementation required** (see below) |
| Go / C# / Java / Kotlin / Scala / Dart | GC | RC not needed (GC manages automatically) |
| TS / JS / Ruby / Lua / PHP / Julia | GC | RC not needed |

Languages with GC do not need RC at all — GC handles both ref classes and containers automatically.

The only language with neither RC nor GC is **Zig**. A `SharedPtr(T)` must be implemented in Zig's Pytra runtime:

```zig
fn SharedPtr(comptime T: type) type {
    return struct {
        ptr: *T,
        rc: *usize,

        pub fn init(allocator: Allocator, value: T) !SharedPtr(T) {
            const p = try allocator.create(T);
            p.* = value;
            const c = try allocator.create(usize);
            c.* = 1;
            return .{ .ptr = p, .rc = c };
        }

        pub fn clone(self: SharedPtr(T)) SharedPtr(T) {
            self.rc.* += 1;
            return self;
        }

        pub fn release(self: *SharedPtr(T), allocator: Allocator) void {
            self.rc.* -= 1;
            if (self.rc.* == 0) {
                allocator.destroy(self.ptr);
                allocator.destroy(self.rc);
            }
        }
    };
}
```

All languages share the same semantics (shared reference + the last holder releases memory). The names differ per language, but the meaning is identical:

| Concept | C++ | Rust | Zig | GC languages |
|---|---|---|---|---|
| Shared reference | `std::shared_ptr<T>` | `Rc<T>` | `SharedPtr(T)` | Not needed |

## 5. Relationship to EAST3

### 5.1 EAST3 union representation

EAST3 holds unions using the following nodes (spec-east.md §6.3-6.4):

- `OptionalType`: canonical form of `T | None`
- `UnionType(union_mode=general)`: general union (`int | str`)
- `UnionType(union_mode=dynamic)`: dynamic union containing `Any/object`
- `NominalAdtType`: closed nominal ADTs like `JsonVal`

### 5.2 emitter responsibilities

- The emitter reads `UnionType` and generates language-specific representations according to the translation table in §3.
- Degrading `UnionType` to `object` is allowed **only when `union_mode=dynamic`**.
- A `union_mode=general` union must never be degraded to `object`.
- `OptionalType` is emitted not as a union but as Optional (`T?`, `Option<T>`, `T | null`, etc.).

### 5.3 isinstance narrowing

EAST3's isinstance narrowing (Unbox nodes) covers ADT pattern matching in all languages:

| EAST3 | Rust | C++ | Go | TS |
|---|---|---|---|---|
| isinstance(x, int) → Unbox | `if let Enum::Int(n) = x` | `std::holds_alternative<int64_t>(x)` | `n, ok := x.(int64)` | `typeof x === "number"` |

The emitter simply reads the Unbox node and generates the language-specific pattern matching syntax.

## 6. Degradation to `object` is Universally Prohibited

Degrading union types to `object` is **universally prohibited**.

- The `Any` type annotation is prohibited in Pytra. There is no entry point that generates `object`.
- Recursive ADTs can also be expressed as ADTs using each language's pointer / RC / GC mechanisms, as described in §4.
- In dynamically typed languages, all variables are already dynamically typed, so no ADT conversion is needed (the language's native representation is used directly).

As a result:
- lowering no longer needs to degrade unions to `object`
- boxing / unboxing nodes disappear
- Auxiliary mechanisms at `object` boundaries — `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT` etc. — become unnecessary
- The emitter does not need an `object` path

## 7. Related

- [spec-east.md](./spec-east.md) §6.3-6.5: TypeExpr / three union classifications / NominalAdtType
- [spec-tagged-union.md](./spec-tagged-union.md): `type X = A | B` declarations
- [spec-boxing.md](./spec-boxing.md): type conversion at Any/object boundaries
- [plan-union-to-nominal-adt.md](../plans/plan-union-to-nominal-adt.md): migration plan
