<a href="../../ja/spec/spec-runtime-decorator.md"><img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

# @runtime / @extern Decorator Specification

Last updated: 2026-03-29
Status: Draft

## 1. Purpose

- Provide a mechanism for declaring "where the implementation lives" for classes and functions in the type-declaration files under `include/`.
- Distinguish between Pytra's internal runtime implementations and external-library implementations using two decorators, `@runtime` and `@extern`.
- Retire the old decorators (`@extern_method`, `@extern_fn`, `@extern_class`, `@abi`) and consolidate under a unified scheme.

## 2. Decorator / Declaration Summary

| Decorator / Declaration | Meaning | rc | type_id | Use case |
|---|---|---|---|---|
| `@runtime("namespace")` | Implementation lives in the Pytra runtime | yes | yes | built_in / std classes and functions |
| `@extern` | Implementation lives outside Pytra's control | no | no | External libraries such as SDL3 |
| `runtime_var("namespace")` | Variable whose implementation lives in the Pytra runtime | — | — | `math.pi`, `sys.argv`, etc. |

### 2.1 Applicable targets

| Target | `@extern` | `@runtime("ns")` | `runtime_var("ns")` |
|---|---|---|---|
| class | Opaque type (no rc) | Pytra built-in class (with rc) | — |
| def | External function | Pytra runtime function | — |
| variable | — | — | Pytra runtime variable |

## 3. `@runtime` Specification

### 3.1 Class declaration

```python
# Example: list.append is handwritten in each language's runtime
@runtime("pytra.core")
class list(Generic[T]):
    def append(self, x: T) -> None: ...
    def extend(self, x: list[T]) -> None: ...
    def pop(self, index: int = -1) -> T: ...
    def sort(self) -> None: ...
    def clear(self) -> None: ...

# Example: Path has its body in pure Python (src/pytra/std/pathlib.py)
@runtime("pytra.std.pathlib")
class Path:
    def __init__(self, value: str) -> None: ...
    def read_text(self) -> str: ...
    def write_text(self, content: str) -> None: ...
    def __truediv__(self, rhs: str) -> Path: ...
```

- The argument to `@runtime("namespace")` is the namespace. The module is determined by combining it with the class name (`pytra.core.list`, `pytra.std.pathlib.Path`).
- All methods inside the class exist on the runtime side. There is no need to attach a decorator to each one individually.
- The symbol for a method is automatically derived from `ClassName.method_name` (e.g., `list.append`).
- The tag is automatically derived from `stdlib.method.method_name` (e.g., `stdlib.method.append`).
- Translating runtime function names (e.g., `list.append` → `py_list_append_mut`) is the responsibility of `mapping.json`.
- The body is `...` (signature only).
- **Whether the implementation lives in a handwritten runtime or in pure Python (automatically converted through the pipeline) is not distinguished.** The resolver and emitter treat both identically. Which file is used at build time is the responsibility of the linker and build system.

### 3.2 Function declaration

```python
# Example with a handwritten runtime
@runtime("pytra.built_in.io_ops")
def len(x: object) -> int: ...

# Example with a pure Python body
@runtime("pytra.built_in.sequence")
def py_range(start: int, stop: int, step: int) -> list[int]: ...
```

- The module is determined by namespace + function name (`pytra.built_in.sequence.py_range`).
- The symbol is automatically derived from the function name (`py_range`).
- The body is `...` (signature only).
- As with classes, no distinction is made between a handwritten runtime and pure Python.

### 3.3 Automatic derivation rules and optional arguments

Only the first argument (namespace) is required for `@runtime`. `symbol` and `tag` are optional; when omitted they are derived automatically.

```python
# When automatic derivation is sufficient (the majority of cases)
@runtime("pytra.core")
class list(Generic[T]):
    def append(self, x: T) -> None: ...

# When symbol / tag need to be overridden (when the Python name differs from the runtime name)
@runtime("pytra.built_in.sequence", symbol="py_range", tag="iter.range")
def range(stop: int) -> list[int]: ...
```

Automatic derivation rules (example: the `extend` method of `class list` under `@runtime("pytra.core")`):

| Item | Derived from | Result | Override |
|---|---|---|---|
| module | namespace + class name | `pytra.core.list` | Not overridable |
| symbol | class name + method name | `list.extend` | Overridable with `symbol=` |
| tag | `stdlib.method.` + method name | `stdlib.method.extend` | Overridable with `tag=` |

For `def py_range` under `@runtime("pytra.built_in.sequence")`:

| Item | Derived from | Result | Override |
|---|---|---|---|
| module | namespace | `pytra.built_in.sequence` | Not overridable |
| symbol | function name | `py_range` | Overridable with `symbol=` |
| tag | `stdlib.fn.` + function name | `stdlib.fn.py_range` | Overridable with `tag=` |

Note: `tag` (`semantic_tag`) may be removed in the future. Since `runtime_module_id` + `runtime_symbol` uniquely identifies the call target, it may be redundant. For now it is kept for compatibility.

### 3.4 Argument passing

- All arguments are passed as rc. No arg mode specification is needed.
- Runtime helpers are implemented in a single pattern that always assumes rc.
- Stripping rc before passing is forbidden because of aliasing issues (e.g., `a.extend(a)`).
- See the "Design discussion on rc and arg mode" section in `plans/p6-extern-method-redesign.md` for details.

### 3.5 Type handling

- Arguments of POD types (`int`, `float`, `bool`, `str`) are passed as value types.
- Container types (`list[T]`, `dict[K,V]`, `set[T]`) and class instances are wrapped in rc.
- This determination is made mechanically from `resolved_type` in EAST3, using the emitter's type-mapping table.

## 4. `runtime_var` Specification

Declares module-level variables (including constants). It uses a function form rather than a decorator, because Python does not allow decorators on variables.

```python
from pytra.std import runtime_var

pi: float = runtime_var("pytra.std.math")
e: float = runtime_var("pytra.std.math")
```

- The namespace is specified as the argument to `runtime_var`.
- The symbol is automatically derived from the variable name (`pi`).
- The tag is automatically derived from `stdlib.symbol.` + variable name (`stdlib.symbol.pi`).

```python
from pytra.std import runtime_var

argv: list[str] = runtime_var("pytra.std.sys")
path: list[str] = runtime_var("pytra.std.sys")
```

### EAST representation

```json
{
  "kind": "AnnAssign",
  "target": {"kind": "Name", "id": "pi"},
  "annotation": "float64",
  "meta": {
    "extern_var_v1": {
      "schema_version": 1,
      "module_id": "pytra.std.math",
      "symbol": "pi",
      "tag": "stdlib.symbol.pi"
    }
  }
}
```

## 5. `@extern` Specification

### 5.1 Opaque classes

```python
@extern
class Window:
    def set_title(self, title: str) -> None: ...
    def close(self) -> None: ...
```

- Not wrapped in rc (opaque handle).
- Not boxed.
- Has no type_id.
- Not subject to isinstance.
- See `spec-opaque-type.md` for details.

### 5.2 External functions

```python
@extern
def sdl_init(flags: int) -> int: ...

@extern
def sdl_create_window(title: str, w: int, h: int, flags: int) -> int: ...
```

- Functions whose implementation lives in the target language.
- Pytra only knows the signature.
- The emitter generates delegation code (a thin wrapper around the native function).

### 5.3 Specifying individual symbols for methods inside an `@extern` class

This is not needed in the vast majority of cases, but it is available when an external library's API name differs from Pytra's method name:

```python
@extern
class Window:
    @extern(symbol="SDL_SetWindowTitle")
    def set_title(self, title: str) -> None: ...
```

### 5.4 External variables (`extern_var`)

Declares constants and variables from external libraries. Uses the same function form as `runtime_var`, symmetrically.

```python
from pytra.std import extern_var

# Python name == external symbol name
WINDOW_SHOWN: int = extern_var()

# Explicit external symbol name
SDL_INIT_VIDEO: int = extern_var("SDL_INIT_VIDEO")
```

- Accepts 0 or 1 argument (symbol name only; namespace is not needed).
- When no argument is given, the Python variable name is used directly as the external symbol name.
- The old form `extern_var(module=..., symbol=..., tag=...)` is rejected fail-closed by the parser.
- The EAST representation reuses the existing `extern_var_v1` schema (`symbol` + `same_name`).

## 5. Structure of `include/` files

```
src/include/py/pytra/
  built_in/
    containers.py     — @runtime("pytra.core") class list, dict, set, tuple
    builtins.py       — @runtime("pytra.built_in.*") def len, print, str, ...
    sequence.py       — @runtime("pytra.built_in.sequence") def py_range, ...
  std/
    pathlib.py        — @runtime("pytra.std.pathlib") class Path
    math.py           — @runtime("pytra.std.math") def sqrt, sin, cos, ... + runtime_var("pytra.std.math") pi, e
    time.py           — @runtime("pytra.std.time") def perf_counter
    json.py           — @runtime("pytra.std.json") def loads, dumps
    sys.py            — @runtime("pytra.std.sys") ...
    os.py             — @runtime("pytra.std.os") ...
    glob.py           — @runtime("pytra.std.glob") ...
```

Each file contains signatures (type annotations) only. The implementations live here:
- `src/pytra/built_in/` — pure Python implementations (converted through the pipeline)
- `src/pytra/std/` — pure Python implementations (converted through the pipeline)
- `src/runtime/<lang>/` — language-specific native implementations (a subset only)

## 6. Retired decorators

| Old | New | Notes |
|---|---|---|
| `@extern_method(module=..., symbol=..., tag=...)` | Method inside a `@runtime` class (auto-derived) | Retired in P0-RUNTIME-DECORATOR |
| `@extern_fn(module=..., symbol=..., tag=...)` | `@runtime("ns") def ...` or `@extern def ...` | Same |
| `@extern_class(module=..., symbol=..., tag=...)` | `@runtime("ns") class ...` or `@extern class ...` | Same |
| `extern_var(module=..., symbol=..., tag=...)` | `runtime_var("ns")` or `extern_var("sym")` | Same |
| `@abi(args={...})` | Retired (arg mode no longer needed) | Same |

The parser halts fail-closed when it encounters an old-style decorator.

## 7. EAST Representation

### @runtime class

```json
{
  "kind": "ClassDef",
  "name": "list",
  "decorators": ["runtime"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "module_id": "pytra.core.list",
      "class_symbol": "list",
      "methods": {
        "append": {"symbol": "list.append", "tag": "stdlib.method.append"},
        "extend": {"symbol": "list.extend", "tag": "stdlib.method.extend"}
      }
    }
  }
}
```

### @extern class

```json
{
  "kind": "ClassDef",
  "name": "Window",
  "decorators": ["extern"],
  "meta": {
    "opaque_v1": {"schema_version": 1}
  }
}
```

### @runtime def

```json
{
  "kind": "FunctionDef",
  "name": "py_range",
  "decorators": ["runtime"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "module_id": "pytra.built_in.sequence",
      "symbol": "py_range",
      "tag": "stdlib.fn.py_range"
    }
  }
}
```

### @extern def

```json
{
  "kind": "FunctionDef",
  "name": "sdl_init",
  "decorators": ["extern"],
  "meta": {
    "extern_v2": {
      "schema_version": 2,
      "symbol": "sdl_init"
    }
  }
}
```

### extern_var

```json
{
  "kind": "AnnAssign",
  "target": {"kind": "Name", "id": "WINDOW_SHOWN"},
  "annotation": "int64",
  "meta": {
    "extern_var_v1": {
      "schema_version": 1,
      "symbol": "SDL_WINDOW_SHOWN",
      "same_name": 0
    }
  }
}
```

- For `extern_var()`: `symbol == target_name` and `same_name == 1`.
- For `extern_var("sym")`: `symbol == <literal>`, and `same_name` is determined by whether the symbol matches the target name.
- Distinguished from the `runtime_var` EAST representation (§4) by the presence or absence of `module_id` / `tag`.

## 8. Resolution Flow in the Pipeline

Declaration files under `include/` are processed through the following flow.

```
src/include/py/pytra/**/*.py
    ↓ parser (generates EAST1)
test/include/east1/py/**/*.east1    ← stored as golden
    ↓ load_builtin_registry() reads during the resolve stage
builtin registry (type-signature dictionary)
    ↓ referenced during EAST1 → EAST2 type resolution
EAST2 (with runtime_call, runtime_module_id, and semantic_tag applied)
```

Responsibility boundaries:

- **parser**: syntactic conversion from `.py` to `.east1` only. Decorators are attached to nodes as raw strings; their meaning is not interpreted.
- **resolve**: reads `.east1`, interprets the semantics of `@runtime`, `@extern`, `runtime_var`, and `extern_var`, and registers them in the builtin registry. When converting user-code EAST1 to EAST2, it references this registry to apply `runtime_module_id`, `runtime_symbol`, `semantic_tag`, and so on.
- **emitter**: renders the already-resolved information from EAST3 only. Re-interpreting decorators is forbidden.

## 9. Declaration Quick Reference

| | runtime (Pytra internal) | extern (external library) |
|---|---|---|
| **Class** | `@runtime("ns") class X:` | `@extern class X:` |
| **Method** | Implicit (no decorator needed) | Implicit (overridable with `@extern(symbol=)`) |
| **Function** | `@runtime("ns") def f():` | `@extern def f():` |
| **Variable** | `x: T = runtime_var("ns")` | `x: T = extern_var("sym")` |
| rc | yes | no |
| type_id | yes | no |
| isinstance | supported | not supported |

## 10. Related

- [spec-opaque-type.md](./spec-opaque-type.md) — details on opaque types (`@extern class`)
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter mapping conventions
- [spec-runtime-mapping.md](./spec-runtime-mapping.md) — mapping.json
- [plans/p6-extern-method-redesign.md](../plans/p6-extern-method-redesign.md) — design discussion history
