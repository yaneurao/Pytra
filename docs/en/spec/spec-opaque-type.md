<a href="../../ja/spec/spec-opaque-type.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Opaque Type Specification (Type Contract for extern classes)

Last updated: 2026-04-03
Status: Finalized (v1)

## 1. Purpose

- Safely handle externally declared classes (`@extern class`) in Pytra's type system.
- Pass handles/pointers from external libraries (such as SDL3) directly without wrapping them in rc.
- Avoid boxing/unboxing.

## 2. Non-Goals

- Field access on opaque types.
- Arithmetic operations on opaque types.
- Inheritance of opaque types.
- Direct constructor calls on opaque types (only factory methods are allowed).

## 3. Definition

A class declared with `@extern class` whose body contains only method signatures is treated as an **opaque type**.

```python
@extern
class Window:
    def set_title(self, title: str) -> None: ...
    def close(self) -> None: ...

@extern
class Renderer:
    def clear(self) -> None: ...
    def present(self) -> None: ...
```

Opaque types have the following characteristics:

- **Not wrapped in rc.** Treated as a native type in the target language (pointer, handle, etc.) directly.
- **Not boxed.** Does not become `Object<void>` / `Any`.
- **Nominal type.** `Window` and `Renderer` are distinct types and cannot be assigned to each other.
- **Has no type_id.** Not subject to isinstance.
- **Only methods declared with `@extern` can be called.** All methods on an opaque type are extern.

## 4. Position in the Type System

EAST type categories:

| Category | rc | boxing | isinstance | Examples |
|---|---|---|---|---|
| POD | none | none | exact match | `int64`, `float64`, `bool`, `str` |
| class | yes | yes | type_id range check | user-defined classes |
| Any / object | yes | yes | — | `Any`, `object` |
| **opaque** | **none** | **none** | **not allowed** | `@extern class Window` |

Opaque types are represented with the same `NamedType` as ordinary classes. No dedicated `OpaqueType` kind is used. Whether a type is opaque is determined by `ClassDef.meta.opaque_v1` and `class_storage_hint: "opaque"`.

```json
{
  "kind": "NamedType",
  "name": "Window"
}
```

The emitter looks at `class_storage_hint` to determine whether rc is required:
- `"ref"` → `shared_ptr` (ordinary class)
- `"value"` → value type
- `"opaque"` → raw pointer, no rc

## 5. What Is and Isn't Allowed

### Allowed

```python
@extern
class App:
    def create_window(self) -> Window: ...
    def destroy_window(self, win: Window) -> None: ...

@extern
class Window:
    def set_title(self, title: str) -> None: ...

if __name__ == "__main__":
    app: App = App()
    win: Window = app.create_window()
    win.set_title("hello")          # OK: calling an extern method on Window
    app.destroy_window(win)          # OK: passing Window to a parameter that expects Window
```

- Passing directly to arguments that expect the same opaque type
- Calling methods declared with `@extern`
- Assigning to variables
- Using as function arguments or return values
- **Putting in containers**: `list[Window]`, `dict[str, Window]`, `set[Window]`
- **Making Optional**: `Window | None` (corresponding to a null pointer)
- **Equality comparison**: `win1 == win2` (treated as pointer comparison)

### Not Allowed

```python
    print(win)                       # NG: cannot convert to str
    x: Any = win                     # NG: cannot box to Any
    isinstance(win, Window)          # NG: isinstance not allowed
    win.width                        # NG: field access not allowed (extern methods only)
    if win:                          # NG: truthiness check not allowed
```

## 6. Mapping to Each Language

| Language | Mapping |
|---|---|
| C++ | Pointer (`Window*`). No rc. |
| Go | Pointer (`*Window`) or unsafe.Pointer. No rc. |
| Rust | `*mut Window` or `Box<Window>`. No rc. |
| Java | Object reference (`Window`). Managed by GC. |
| C# | Object reference (`Window`). Managed by GC. |
| JS/TS | As-is (`Window`). Managed by GC. |

In GC languages, "no rc" is natural (the GC handles it). In C++/Rust/Go, the type is treated as a raw pointer and lifetime management is the responsibility of the external library.

## 7. EAST Representation

### extern class declaration

```json
{
  "kind": "ClassDef",
  "name": "Window",
  "decorators": ["extern"],
  "meta": {
    "opaque_v1": {
      "schema_version": 1
    }
  },
  "body": [
    {
      "kind": "FunctionDef",
      "name": "set_title",
      "decorators": ["extern"],
      "args": [{"name": "self"}, {"name": "title", "type": "str"}],
      "return_type": "None"
    }
  ]
}
```

### Variable of opaque type

Opaque type variables are represented with the same `NamedType` as ordinary classes. The `OpaqueType` kind is not used.

```json
{
  "kind": "Name",
  "id": "win",
  "resolved_type": "Window",
  "type_expr": {
    "kind": "NamedType",
    "name": "Window"
  }
}
```

### Method call on an opaque type

Methods on an opaque type are represented as ordinary `Call` + `Attribute`. They are resolved as `@extern` methods.

## 8. Decisions (Finalized 2026-04-03)

- **`list[Window]` is allowed.** The list is managed with rc, but each Window element is a raw pointer. In C++ this becomes `list<Window*>`.  compile/resolve must not degrade the opaque type to `object`; it must be kept as `NamedType("Window")`.
- **`Optional[Window]` (`Window | None`) is allowed.** A natural representation of a null pointer. In C++, `Window*` can already be `nullptr`, so no additional cost.
- **Equality comparison (`win1 == win2`) is allowed.** Treated as pointer comparison.
- **Constructor calls (`Window()`) are only allowed via factory methods.** The internal structure of an opaque type is unknown, so direct construction is not possible. Use factory patterns like `App.create_window()`.
- **An `@extern class` with fields is not opaque.** An `@extern class` with fields is treated as a regular extern class (`class_storage_hint: "ref"`) and is distinct from an opaque type. Opaque types have only method signatures.

## 9. Related

- [spec-type_id.md](./spec-type_id.md) — type_id specification (opaque types have no type_id)
- [spec-east.md](./spec-east.md) — EAST node specification
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter mapping conventions
- [plans/p6-extern-method-redesign.md](../plans/p6-extern-method-redesign.md) — @runtime / @extern redesign
