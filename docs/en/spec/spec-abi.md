<a href="../../ja/spec/spec-abi.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Pytra Transpiler Specification: `@extern` / `@abi` and Fixed ABI Types (C++ Backend)

Notes:

- `@extern` is a canonical feature of the current implementation.
- `@abi` is an approved next-step extension, and this document defines its target design.
- Before `@abi` is implemented, generated runtime helpers follow the ordinary internal-representation rules.
- For `@abi`, this document is the source of truth for syntax / semantics / modes / the responsibility split from `@extern`; the parser/EAST metadata format is fixed separately by `P1-RUNTIME-ABI-DECORATOR-01-S1-02`.

## 1. Objective

Pytra is a transpiler from Python to C++ and other languages. Inside the C++ backend, ownership forms such as `rc<T>` are used to manage object lifetimes.

Because of optimization during translation, the same Python type may map to multiple internal C++ representations. For example:

- `rc<list<rc<bytearray>>>` -> `list<rc<bytearray>>`
- `list<rc<bytearray>>` -> `list<bytearray>`

This drift becomes a problem at the following two boundaries:

- `@extern` functions delegated to external implementations defined on the C++ side
- generated runtime helpers that should require a fixed ABI shape rather than an internal representation

`@extern` functions must always be callable with the same boundary types regardless of the internal representation at the call site. Likewise, some generated helpers, such as `str.join`, need a fixed value ABI.

This specification solves that by separating:

- the external-implementation marker `@extern`
- the generated/helper boundary ABI override `@abi`

and giving each a **fixed ABI type**, while inserting **ABI adaptation** at the call site only when required.

Important:

- `rc<T>` is an internal ownership form of the C++ backend, not the ABI itself.
- Value/container ABI types such as `str`, `bytes`, `bytearray`, `list[T]`, `dict[K,V]`, `set[T]`, and `tuple[...]` must **not expose `rc<>`**.
- `rc<>` may be used in the ABI only for types whose reference semantics are essential, such as user classes.
- The backend may still use typed handles such as `rc<list<T>>` for internal optimization and alias preservation, but these are **internal types**, not ABI types.
- In particular, even when `rc<list<T>>` is used to preserve aliases under `cpp_list_model=pyobj`, the `@extern` boundary must normalize it to `list<T>`.

This specification supports only **argument-less `@extern`**.  
`@abi` does not replace `@extern`; it is an orthogonal helper annotation.

## 2. Terms

- **Internal Type**  
  The actual C++ representation type used during optimization and lowering. Multiple patterns may exist after optimization.  
  Examples: `list<bytearray>`, `rc<list<bytearray>>`, `object`

- **ABI Type**  
  The fixed C++ type used at an `@extern` boundary. It must match the function signature defined by the external implementation (runtime / target-language side).

- **ABI Adaptation**  
  The conversion inserted at a call site from the internal type to the ABI type. It is inserted only when necessary, including no-op cases.

- **Value ABI**  
  Boundary types that do not contain `rc<>`, such as `str`, `bytes`, `bytearray`, `list[T]`, `dict[K,V]`, `set[T]`, and `tuple[...]`.

- **Reference ABI**  
  Boundary types that preserve identity or dynamic dispatch, such as user classes and `object`.

## 3. Basic `@extern` specification

### 3.1 Syntax

Only the following Python-side forms are allowed.

```python
@extern
def write_png(image: list[bytearray]) -> None: ...
```

```python
from pytra.std import extern

@extern
def write_png(image: list[bytearray]) -> None: ...
```

`extern` is only a marker and behaves as a no-op at Python runtime.

```python
def extern(fn):
    return fn
```

- In current v1, argumented decorators such as `@extern(...)` are not supported.
- In v2, it is split into `extern_fn` / `extern_var` / `extern_class`, with required arguments `module` / `symbol` / `tag`. See [spec-builtin-functions.md §10](./spec-builtin-functions.md) for details.
- An extern marker on a variable is written in `name = extern(...)` form.
- `name: Any = extern()` is treated as a declaration of an ambient global variable with the same name.
- `name: Any = extern("symbol")` is treated as a declaration of an ambient global variable under another symbol name.
- `name: T = extern(expr)` remains the existing host fallback / runtime-hook initialization form.
- Ambient-global variable declarations are allowed only on JS/TS backends in v1; other backends must raise compile errors.
- runtime-SoT `@extern` is declaration-only metadata and does not represent the owner of the target implementation.
- runtime layout / manifest / runtime symbol index determine where the native owner implementation lives.
- Ambient-global variable declarations via `extern()` / `extern("symbol")` are handled separately from runtime `@extern`.

### 3.2 Meaning

A function annotated with `@extern` is delegated to a handwritten implementation provided on the target-language side.

For an `@extern` function, Pytra determines:

- the external name (symbol name)
- the ABI type

At the call site, even if actual arguments are represented with internal types, the transpiler adapts them into ABI types before calling the external function.

For Python-runtime compatibility, an `@extern` function may still have a Python-executable body, for example `return __m.sin(x)`. The transpiler never adopts that body as the target implementation; it lowers the function into an external-symbol call instead.

#### 3.2.1 Per-language realization of `@extern`

The realization of `@extern` differs between C++ and other languages.

**C++**: emit declarations only + link/include integration

- The emitter outputs only the **declaration (prototype)** of an `@extern` function into `.h`.
- The handwritten implementation exists in `src/runtime/cpp/{built_in,std}/*.h` and is connected through `#include`.
- Since C++ link/include machinery integrates declaration and implementation, no delegation wrapper is needed.
- The handwritten implementation may freely use templates and overloads, including C++-specific features not representable in EAST3.

**Other languages (JS, Dart, Julia, Zig, PowerShell, etc.)**: generate delegation code

- For an `@extern` function, the emitter generates **delegation code** to a `_native` module.
- Delegation target: `<module>_native.<ext>` (for example `time_native.js`, `math_native.dart`)
- Example generated code (JS):
  ```javascript
  // std/time.js (generated)
  const time_native = require("./time_native.js");
  function perf_counter() { return time_native.perf_counter(); }
  ```
- The `_native` file is handwritten and provides the minimum host-API connection code.
- It is assumed that compiler optimization (such as inlining) makes the delegation cost effectively negligible.

Reason for this difference:

- The handwritten C++ runtime makes heavy use of templates, overloads, and other C++-specific features, so auto-generating delegation wrappers from EAST3 is difficult.
- In other languages, function-call delegation is sufficient and can be handled with a unified mechanism.

Variable `extern(...)` forms are handled separately from function `@extern`.

- `extern(expr)`:
  - keeps `expr` as the Python-runtime fallback / host-only initializer
- `extern()`:
  - declares an ambient global under the same variable name, with no Python fallback
- `extern("symbol")`:
  - declares an ambient global under the given string symbol, with no Python fallback

JS/TS lower ambient-global variable declarations as import-free symbols. Raw lowering of property access / method calls / call expressions is allowed only for bindings marked as ambient globals, not as a general `Any/object` relaxation.

runtime-SoT `@extern` remains declaration-only metadata.

- `extern_contract_v1` / `extern_v1` describe only the declared symbol shape and do not encode the location of the native owner implementation.
- runtime layout / manifest / runtime symbol index determine the owner implementation location.
- Ambient-global variable declarations via `extern()` / `extern("symbol")` are a different category from runtime-SoT `@extern` and must not be mixed into owner resolution.

### 3.3 Host-only import rule (`as __name`)

Imports such as `import ... as __m` are treated as host-only imports.

- A host-only import is used only for Python-runtime support, such as evaluating the Python body of an `@extern` function.
- It is not emitted into target-language code.
- References to the host-only alias are allowed only inside an `@extern` function body or an `extern(expr)` initializer.
- Using `__m` anywhere else is a compile error.
- `_name` with a single leading underscore is not host-only and is treated as a normal import.

### 3.4 Basic `@abi` specification (approved extension)

#### 3.4.1 Objective

`@abi` is used when the boundary signature of a generated/runtime helper must be fixed.

Its purpose is different from `@extern`.

- `@extern`
  - fixes the implementation location to an external implementation
- `@abi`
  - fixes only the boundary ABI shape; the implementation may be generated or external

Therefore `@abi` must not absorb `@extern` through notions such as `no_body` or `external`.

#### 3.4.2 Syntax

```python
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

In the initial scope, only the following form is supported:

- keyword arguments only
- `args={param_name: mode}`
- `ret=mode`

Unsupported:

- positional forms such as `@abi("value")`
- application to classes, methods, lambdas, or nested functions
- general exposure to all user programs

The initial target may be limited to top-level helpers in runtime SoT modules (`src/pytra/built_in/*.py`, and `std/utils` if needed).

At Python runtime, `abi` behaves as a no-op decorator.

```python
def abi(*, args=None, ret="default"):
    def deco(fn):
        return fn
    return deco
```

#### 3.4.2.1 Initial acceptance conditions

In the initial rollout, the parser/validator may accept only forms that satisfy all of the following:

- applied to a top-level function
- keyword-only `@abi(args=..., ret=...)`
- keys in `args` match actual parameter names
- canonical modes are one of `default`, `value`, or `value_mut`
- canonical return modes may be only `default` or `value`
- the source surface may accept `value_readonly` as a migration alias, but canonical metadata must normalize it to `value`

The following are compile errors:

- unknown modes
- ABI overrides for undeclared parameter names
- positional forms such as `@abi("value")`
- application to methods, classes, lambdas, or nested functions
- early use in general user code outside runtime helpers

#### 3.4.3 Meaning of `@abi`

`@abi` does not act on the whole function at once. It acts **per parameter** and **per return value**.

Reasons:

- immutable parameters such as `str` do not need an override
- only mutable containers such as `list[str]` may need a fixed value ABI
- some cases need a different policy only for the return value

Therefore the canonical form is:

```python
@abi(args={"parts": "value"}, ret="value")
```

#### 3.4.4 Initial modes

The initial rollout defines the following three modes:

- `default`
  - no override
  - follow the existing internal representation / backend default policy
- `value`
  - fix the return value, or a parameter, to the canonical value ABI
  - in parameter position, this means a read-only value ABI
  - the callee must not mutate the argument destructively
- `value_mut`
  - fix a parameter to a writable value ABI
  - explicitly marks rare mutable value-helper boundaries

Notes:

- `value` is especially important for C++ `list/dict/set/bytearray`.
- It means “do not accept `rc<>` at the ABI boundary,” not “always copy.”
- The C++ backend may use declaration forms such as `const list<T>&` or `const dict<K,V>&`, borrowing read-only from internal handles when possible.
- `value_mut` is a reserved public mode for writable cases, and there are no checked-in helper examples yet.

Out of scope for the initial rollout:

- `internal_ref`
- receiver-only annotations

If they become necessary, extend them in a separate task.

#### 3.4.4.1 Migration rules

- Canonical public naming is `default`, `value`, `value_mut`.
- For parameters, `value` inherits the old meaning of `value_readonly`.
- For returns, `value` still means a value-return ABI.
- `value_readonly` is removed from the canonical surface.
  - The source parser may still accept it as a migration alias.
  - Even then, `FunctionDef.meta.runtime_abi_v1` must normalize it to `value`.
- The old candidate name `value_mutating` is not adopted. The public name for writable cases is `value_mut`.

#### 3.4.5 Relationship with `@extern`

`@abi` and `@extern` are independent and may be combined.

```python
@extern
def sin(x: float) -> float:
    return __m.sin(x)
```

```python
@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

```python
@extern
@abi(args={"image": "value"}, ret="value")
def some_native_helper(image: list[bytearray]) -> bytes:
    ...
```

Meaning:

- with `@extern`
  - the body is not generated; lowering goes to an external symbol
- with `@abi`
  - the boundary ABI form is overridden
- with neither
  - ordinary internal-representation rules and backend default lowering apply

#### 3.4.6 Why `str.join` needs it

In the current C++ runtime, `str.join` is intended to use a value ABI close to `str::join(const list<str>& parts)`.

If the helper is generated naively, however, the C++ backend's ref-first internal model may drift `list[str]` toward `rc<list<str>>`. That conflicts with the goal of moving the helper back into pure Python SoT.

Therefore a helper such as `py_join` must be fixed with `@abi`.

```python
@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

With that annotation, in C++:

- `parts` is treated as a helper receiving the canonical ABI form `list<str>`
- the actual declaration may still use `const list<str>&`
- the call site inserts a read-only adapter if it sees `rc<list<str>>`

#### 3.4.7 Constraints

- `@abi` fixes helper ABI only. It does not define module imports, symbol resolution, or semantic tags.
- `@abi` must not leak source-side module knowledge into the backend.
- Even when `@abi` is present, the function must not be treated as an external implementation unless `@extern` is also present.
- A contradiction between an `@abi` mode and the function body is a compile error.
  - for example, `append`, `pop`, or assignment against an argument marked `value`
- `@abi` is fail-closed. If a backend/lowerer does not understand the mode, compilation must fail.

#### 3.4.8 EAST / linked metadata shape

`@abi` must be retained not only as decorator syntax but also as function-node metadata.

Raw EAST / raw EAST3 must carry at least:

- `FunctionDef.decorators`
  - may preserve the raw decorator string such as `abi(args={"parts": "value"}, ret="value")`
- `FunctionDef.meta.runtime_abi_v1`
  - canonical metadata for backends and the linker

Canonical metadata shape:

```json
{
  "schema_version": 1,
  "args": {
    "parts": "value"
  },
  "ret": "value"
}
```

Rules:

- `schema_version` is required and must be `1`
- `args` is a parameter-name -> mode map
- `ret` is the return mode
- canonical modes are only `default`, `value`, and `value_mut`
- `ret` allows only `default` or `value`, never `value_mut`
- even when the source surface accepts `value_readonly`, canonical metadata must normalize it to `value`
- keys in `args` may be normalized to source parameter order
- omitted `ret` means `default`
- omitted `args` means an empty map

After linked-program processing, `FunctionDef.meta.runtime_abi_v1` must still be preserved, and the linker must not rewrite it. The linker may add only module-level `meta.linked_program_v1` or call/function summaries; the helper ABI contract itself remains sourced from parser/EAST build.

Parser/selfhost-parser acceptance contract:

- the same source must produce the same `runtime_abi_v1` in both implementations
- unsupported forms are rejected fail-closed during EAST1/EAST2 build
- even if raw `abi(...)` stays in `decorators`, the only canonical source a backend may read is `meta.runtime_abi_v1`

## 4. External name (symbol name) rule

For an `@extern` function `M.f`, the external symbol name is:

```text
pytra_<module>_<function>
```

- `<module>` is the Python module name, such as `pytra.std.math` or `pytra.utils.png`
- `<function>` is the function name

Examples:

- `pytra.std.math.sin` -> `pytra_std_math_sin`
- `pytra.utils.png.write_png` -> `pytra_utils_png_write_png`

Notes:

- The module name must be determined uniquely from the package name.
- Nested or local functions are out of scope.
- `@extern` may be limited to top-level functions only.
- runtime-SoT `@extern` is declaration-only metadata and does not represent the target implementation owner.
- runtime layout / manifest / runtime symbol index determine where the native owner implementation lives.
- ambient-global variable declarations via `extern()` / `extern("symbol")` are handled separately from runtime `@extern`.

## 5. ABI type determination rule

### 5.1 Basic policy

The ABI type is a fixed C++ type derived from the Python type annotation. It must not drift under internal optimization.

Treat ABI types as canonical boundary forms.

Mandatory rules:

- the ABI must **not expose internal ownership forms**
- value/container ABI types must not use `rc<>`
- `rc<>` is allowed in the ABI only for reference types that must preserve identity, such as user classes
- `rc<list<T>>` is only an internal alias-preservation / optimization form and is not part of the canonical ABI

`@abi` modes such as `value` and `value_mut` are the annotations that explicitly apply this canonical ABI form to helper boundaries.

### 5.1.1 Default policy for backend internal representations

The canonical ABI form and the initial internal backend representation are separate concerns.

Mandatory rules:

- immutable types such as `str` may use value representation internally by default
- mutable types such as `list`, `dict`, `set`, and `bytearray`, and mutable user classes, must use a representation that preserves shared references by default
- in the C++ backend, that shared-reference form may be `rc<>` or an equivalent handle
- however, that `rc<>` is only an internal representation and must not leak into the ABI

Value lowering is allowed only as an optimization result.

- do not lower mutable values that can exhibit aliasing (`a = b`) into value types without proof
- value lowering requires safety proof across mutation / alias / escape analysis
- interprocedural lowering requires call-graph construction and SCC-level summaries for recursion / mutual recursion
- paths crossing `Any/object`, `@extern`, unknown calls, or unresolved types must fail closed and remain in shared-reference form

In short: the ABI stays fixed to value-shaped canonical forms such as `list<T>`, while the backend internally uses mutable types in ref-first form and lowers only proven-safe paths afterward.

### 5.2 Canonical value ABI forms

Recommended canonical forms in this specification:

```text
bool -> bool

int -> int64
  In Pytra, Python `int` is treated as signed 64-bit integer (`int64`).

float -> float64

str -> str

bytes -> bytes

bytearray -> bytearray

list[T] -> list<ABI(T)>

dict[K,V] -> dict<ABI(K), ABI(V)>

set[T] -> set<ABI(T)>

tuple[T1, T2, ...] -> std::tuple<ABI(T1), ABI(T2), ...>

None (return) -> void
```

Here `ABI(T)` means the canonical ABI form of the element type.

Important:

- the ABI of `list[str]` is `list<str>`, not `list<rc<str>>`
- the ABI of `list[bytearray]` is `list<bytearray>`, not `rc<list<rc<bytearray>>>`
- the ABI of `dict[str, int]` is `dict<str, int64>`
- even if the internal form of `list[int]` is reduced to `rc<list<int64>>`, the ABI stays `list<int64>`

### 5.3 Canonical reference ABI forms

The following may be treated as reference ABI types rather than value ABI types:

```text
Any / object -> object

user class C -> rc<C>

runtime objects that require identity -> current runtime reference type
```

Examples:

- `Animal` -> `rc<Animal>`
- `Token` -> `rc<Token>`
- `object` / `Any` -> `object`

So `rc<>` is not globally banned; it is forbidden only for value ABI.

### 5.4 C++ parameter declaration forms

The ABI type itself and the concrete C++ declaration form are separate concerns.

Example:

- ABI type: `list<bytearray>`
- possible C++ declaration forms:
  - `const list<bytearray>& image`
  - `list<bytearray> image`
  - `list<bytearray>& image`

Which declaration form to use depends on mutation, copy cost, and backend policy.  
However, **the canonical element form (`list<bytearray>`) must not change**.

## 6. ABI adaptation rules

### 6.1 Insertion point

When lowering an `@extern` call or an `@abi`-annotated helper call into an ABI-fixed boundary, for each argument:

1. obtain the internal type `Tin` of the actual argument
2. obtain the fixed ABI type `Tabi`
3. if `Tin == Tabi`, pass it directly
4. otherwise insert `adapt(Tin -> Tabi)` and pass the result

### 6.2 Adaptation function shape

Adaptation may be expressed in generated code like:

```cpp
adapt_to_abi<list<bytearray>>(x)
```

The concrete function name is backend-defined, but its role is limited to:

- normalization from internal type to fixed ABI type
- no unnecessary conversion when the mapping is a no-op

### 6.3 Required conversion cases (example: `list[bytearray]`)

For `Tabi = list<bytearray>`, at least the following must be handled.

#### Case 1: `Tin = list<bytearray>`

-> no-op

#### Case 2: `Tin = list<rc<bytearray>>`

-> normalize each element to `bytearray` and construct `list<bytearray>`

#### Case 3: `Tin = rc<list<bytearray>>`

-> strip the outer `rc<>` and construct `list<bytearray>`

#### Case 4: `Tin = rc<list<rc<bytearray>>>`

-> strip the outer `rc<>`, normalize each element to `bytearray`, and construct `list<bytearray>`

Other incoming types may be treated as compile errors.

### 6.4 Additional rule for `@abi(args={"x": "value"})`

For a parameter `x` annotated with `@abi(args={"x": "value"})`, the backend must obey:

- the canonical ABI form is value ABI
- the target-language declaration may use a read-only borrow
- in C++, `const T&` is allowed
- if a read-only borrow from an internal handle such as `rc<list<T>>` is possible, do not insert an unnecessary copy
- if borrowing is impossible, insert an adapter fail-closed

### 6.5 Additional rule for `@abi(args={"x": "value_mut"})`

For a parameter `x` annotated with `@abi(args={"x": "value_mut"})`, the backend must obey:

- the canonical ABI form is value ABI
- the callee may mutate the argument destructively
- adapter elision via read-only borrow is forbidden
- when the target cannot express a writable borrow, insert an adapter/copy fail-closed

### 6.6 Additional rule for `@abi(ret="value")`

`ret="value"` fixes the return value to the canonical value ABI.

This prevents generated helpers from leaking internal ref-first representations directly across the boundary.

### 6.7 Adaptation cost policy

ABI adaptation may involve copying or reconstruction, but the governing policy is:

- prioritize a fixed ABI at external boundaries
- insert conversions only when required
- functions such as `write_png` are I/O-oriented and usually do not make boundary copies dominant
- if performance becomes a problem, design a dedicated ABI such as span / pointer + size / writable buffer case by case

## 7. Generated C++ declarations and linking

### 7.1 How declarations are provided

External function declarations may be provided in either of the following ways:

- Method 1: the transpiler auto-generates forward declarations only for used external functions
- Method 2: a common header is always included and contains the declarations

Both are permitted, but Method 1 is recommended initially.

### 7.2 About `extern "C"`

The “ABI” in this document means **Pytra’s fixed boundary types**, not plain C ABI.

Therefore:

- `extern "C"` may be used to suppress name mangling
- but when types such as `list<bytearray>` or `dict<str, int64>` appear, that does not mean the function is directly callable from C

`extern "C"` is optional, but acceptable for symbol-name stabilization.

## 8. Specification constraints

- An `@extern` function may use a stub body (`...` / `pass`) or a Python-executable body.
- When lowered into the target language, its body is replaced by the external implementation.
- It is recommended that `@extern` functions require type annotations for parameters and returns.
- `@extern` may be restricted to top-level functions only.
- The usage restriction on `import ... as __name` (host-only import) is mandatory.

## 9. Example (`write_png`)

Python:

```python
from pytra import extern

@extern
def write_png(image: list[bytearray]) -> None: ...
```

ABI types:

- `image: list<bytearray>`
- return: `void`

Generated conceptually:

```cpp
// example forward declaration
extern "C" void pytra_utils_png_write_png(const list<bytearray>& image);

void callsite(...) {
    // image_in may drift by optimization, e.g. rc<list<rc<bytearray>>>
    auto image_abi = adapt_to_abi<list<bytearray>>(image_in);
    pytra_utils_png_write_png(image_abi);
}
```

External implementation:

```cpp
extern "C" void pytra_utils_png_write_png(const list<bytearray>& image) {
    // PNG write logic
}
```

## 10. Implementation checklist

- detect functions annotated with `@extern` from AST / EAST
- derive ABI types uniquely from Python type annotations
- derive the external name `pytra_<module>_<func>` uniquely
- compare `(Tin, Tabi)` at call sites and insert `adapt` when needed
- normalize representative cases such as `list[bytearray]` into the ABI despite multiple internal forms
- generate external function declarations (forward declarations or runtime headers)

## 11. Runtime directory layout assumed by this specification

The canonical runtime layout follows `docs/ja/spec/spec-runtime.md`.

Restricting this to the key points assumed by this document, the current C++ runtime uses the following ownership lanes:

- `runtime/cpp/generated/{built_in,std,utils,compiler}/`
- `runtime/cpp/native/{built_in,std,utils,compiler}/`
- `runtime/cpp/generated/core/`
- `runtime/cpp/native/core/`

Ownership rules:

- declarations and thin wrappers generated from the SoT live under `generated/`
- minimum native implementations that connect to the OS / SDK / C++ standard library live under `native/`
- low-level core splits ownership between `generated/core` and `native/core`

Notes:

- Ownership of the C++ module runtime is identified by directory, not suffix.
- The old suffix-based module runtime under `src/runtime/cpp/{built_in,std,utils}` is legacy-closed and must not be reintroduced.
- `core` is also split between `runtime/cpp/generated/core/` and `runtime/cpp/native/core/`, and there must be no checked-in `runtime/cpp/core/*.h`.
- The ABI model itself does not change.
- Follow `docs/ja/spec/spec-runtime.md`, `docs/ja/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md`, and `docs/ja/plans/p0-cpp-core-ownership-split.md` for details.

## 12. Example: `pytra.std.math`

`src/pytra/std/math.py` contains `@extern`. Its structure by language:

**C++** (declarations + linker/include integration):

- handwritten implementation: `src/runtime/cpp/std/math.h` (the bodies of `@extern` functions)
- the emitter outputs only the declarations of `@extern` functions and connects the handwritten implementation through `#include`

**JS / Dart / Julia etc.** (generated delegation code):

- handwritten native: `src/runtime/<lang>/std/math_native.<ext>` (host-API connection)
- generated by the emitter: `std/math.<ext>` (`@extern` functions delegate to `math_native`)
- example (JS): `function sqrt(x) { return math_native.sqrt(x); }`

Common principles:

- ABI types are fixed to canonical value forms.
- The Python body of an `@extern` function is not used as the target implementation.
- `rc<>` is confined to internal representation, not the ABI.
- The ownership split between `generated/` and `native/` directories has already been established (see `spec-runtime.md §0.6a`).
