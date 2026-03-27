<a href="../../ja/spec/spec-template.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Template Specification (Draft)

This document defines Pytra's generic/template direction.
As of 2026-03-08, v1 treats `@template("T", ...)` written directly in `.py` as the canonical syntax, limited to linked runtime helpers.

> Status cross-check (2026-02-23):
> - Adopted: `typing.TypeVar` remains annotation-only and does not provide template functionality.
> - Adopted: linked runtime helper v1 uses `@template("T", ...)` and does not use `TypeVar`.
> - Pending: `@instantiate`, compile-time branching, instantiation errors, generation limits, and the broader template body design.
> - Rejected: wording that states the notation is already "adopted" in the implementation when it is still a staged design.

## 0. v1 Scope (2026-03-08)

- The canonical syntax is `@template("T", ...)`.
- v1 is limited to top-level runtime helper functions that are included in linked-program processing.
- v1 does not introduce `@instantiate(...)`; specialization/monomorphization is handled later in the linked-program pipeline.
- `typing.TypeVar` remains annotation-only and is not used as the function-scoped generic surface.
- Class generics, method generics, and general user-code exposure are out of scope for v1.

### 0.1 Metadata / Validation (v1)

- The canonical metadata is `FunctionDef.meta.template_v1`.
- Canonical shape:
  - `schema_version: 1`
  - `params: [template_param_name, ...]`
  - `scope: "runtime_helper"`
  - `instantiation_mode: "linked_implicit"`
- Raw `decorators` preserve source surface only. Parser/linker/backend must treat `meta.template_v1` as the source of truth.
- Syntactic validation is performed in parser/EAST build and rejects at least:
  - empty `@template()`
  - non-string-literal identifiers
  - duplicate parameter names
  - multiple `@template` decorators on the same function
  - method / nested function / class application
- The `runtime helper only` restriction is enforced canonically by the linked-program validator. Raw parse may attach metadata to a syntactically valid top-level function, but linked-program validation must fail closed if the module is not a runtime-helper provenance module.
- `TypeVar` annotations alone must not create `meta.template_v1`.

### 0.2 Future `@instantiate(...)` Extension

- The canonical syntax family begins with `@template("T", ...)`, and future explicit instantiation extends the same decorator family with `@instantiate(...)`.
- The minimum future shape is:
  - `@instantiate("symbol_name", type_arg1, type_arg2, ...)`
- v1 does not implement `@instantiate(...)` in parser, validator, linker, or backend.
- The surface must not fork into `TypeVar` or bracket syntax; `@template` remains the canonical family.

### 0.3 Specialization Collector / Monomorphization Connection

- `FunctionDef.meta.template_v1` is syntax metadata and is the canonical input read by the specialization collector after linked-program loading.
- The collector decides specialization seeds from `meta.template_v1` plus concrete type tuples at call sites, not from raw `decorators`.
- Because v1 has no explicit instantiation, `instantiation_mode: "linked_implicit"` means the linked-program collector deterministically gathers concrete type tuples and triggers monomorphization.
- Even after `@instantiate(...)` is introduced, the collector entry remains `meta.template_v1`, with explicit seeds added via separate metadata.

## 1. Objective

- Allow generic functions/classes to be defined on the Python side and translated safely into C++ and other target languages.
- Reduce fallback to `object` and preserve static types in generated code.
- Enable template-incompatible or template-limited languages to generate specialized code via monomorphization.

## 2. Non-goals

- Full reproduction of Python `typing`.
- Full compatibility with higher-kinded types, partial specialization, or metaprogramming.
- Reproducing runtime type-erasure-based dynamic dispatch.

## 3. Basic Policy

- Preserve generic/template information in EAST.
- Use monomorphization (explicit instantiation) for languages whose native template support is weak.
- Prefer explicitly enumerated instantiations rather than unbounded implicit exploration.
- In the long-term design, callers use instantiated symbols rather than calling the template body directly.

## 4. Terms

- template definition: a function/class definition with type parameters
- instantiation: binding concrete type arguments and generating concrete code
- instantiated symbol: the concrete symbol used after instantiation

## 5. `.py` Notation (Long-Term Design)

### 5.1 Basic API

- `pytra.std.template` provides the following decorator family:
  - v1: `@template("T", "U", ...)`
  - future extension: `@instantiate("instantiated_name", type_arg1, type_arg2, ...)`
- `@template` applies only to the immediately following `def` or `class`.
- `@instantiate` is stacked in the same decorator group immediately above the same definition.

### 5.2 Template Function Definition

```python
from pytra.std.template import template, instantiate

@template("T")
@instantiate("add_i64", int64)
@instantiate("add_f64", float64)
def add(a: T, b: T) -> T:
    return a + b
```

### 5.3 Template Class Definition

```python
from pytra.std.template import template, instantiate

@template("T")
@instantiate("Vec2_f64", float64)
class Vec2:
    x: T
    y: T

    def __init__(self, x: T, y: T) -> None:
        self.x = x
        self.y = y
```

### 5.4 Usage Rules (Long-Term Design)

- v1 does not yet decide whether direct use of the template body is allowed.
- In the long-term design, calls/construction use symbols declared by `@instantiate`.
- In the long-term design, direct use such as `add(...)` or `Vec2(...)` is forbidden (`explicit` policy).
- In the long-term design, the first argument of `@instantiate("name", ...)` is the generated instantiated symbol name.

### 5.5 Compile-Time Branches

Inside a template body, compile-time branching may use:

```python
# Pytra::if T == int64
...
# Pytra::elif T == str
...
# Pytra::else
...
# Pytra::endif
```

- `# Pytra::if` / `# Pytra::elif` / `# Pytra::else` / `# Pytra::endif` must be used as a set.
- The left side may only be a template type parameter such as `T`, `K`, or `V`.
- Only `==` / `!=` are allowed in v1.
- The right side is a type token such as `int64`, `str`, or `float64`.
- Quoted type names are acceptable only as compatibility input; the canonical form is unquoted.
- Evaluation happens per instantiation, and only the selected block survives.

## 6. Syntax Constraints

- `@template` / `@instantiate` are allowed only on top-level `def` / `class`.
- `@template("...")` arguments must be string-literal identifiers.
- The first argument of `@instantiate("name", ...)` must be a string-literal identifier.
- The number of type arguments in `@instantiate` must match the number of `@template` parameters.
- `# Pytra::if`-family directives are allowed only inside template bodies.
- v1 forbids nesting of compile-time branch directives.

## 7. Resolution Rules

- Instantiated symbols are defined by `@instantiate("name", type_args...)`.
- Duplicate instantiated names inside the same template definition raise `input_invalid(kind=symbol_collision)`.
- Duplicate type-argument tuples inside the same template definition raise `input_invalid(kind=duplicate_instantiation)`.
- Direct calls to the template body raise `input_invalid(kind=missing_instantiation)` in the explicit long-term model.
- Compile-time branch directives are evaluated per instantiation before normal lowering.

## 8. Name Generation (Mangling)

- Instantiated symbols are converted into unique names including type arguments.
- Recommended format:
  - `__pytra__<module>__<symbol>__<type1>__...`
- Characters outside `[A-Za-z0-9_]` are replaced with `_xx` (two-digit hex).
- Name collisions raise `input_invalid(kind=symbol_collision)`.

## 9. Target-Language Output Policy

- Languages with strong native templates, such as C++/Rust:
  - may allow `native` output or `explicit` output
- Languages without practical native templates:
  - default to `explicit` output
- In every language, the `.py`-side `@instantiate(...)` declarations are the source of truth, not external definition files

## 10. Type Constraints

- Do not allow implicit degradation to `Any` / `object` inside template bodies.
- Type arguments are limited to canonical EAST types such as `int64`, `float64`, `str`, and `list[T]`.
- If unresolved or unknown types remain, stop with `inference_failure`.

## 11. Error Contract

Template-related failures use:

- `input_invalid(kind=missing_instantiation)`
- `input_invalid(kind=duplicate_instantiation)`
- `input_invalid(kind=symbol_collision)`
- `input_invalid(kind=unsupported_type_argument)`
- `input_invalid(kind=invalid_instantiation_form)`
- `input_invalid(kind=invalid_compile_time_branch)`
- `input_invalid(kind=unmatched_compile_time_branch)`
- `input_invalid(kind=unbound_template_param)`
- `unsupported_syntax` for unsupported forms

Error details must include at least `module`, `symbol`, `type_args`, and `source_span`.

## 12. Generation Limit Guard

To prevent specialization explosion:

- `--max-instantiations N` limits the total number of instantiated symbols produced in one translation
- the count includes indirectly triggered instantiations as well
- the limit is on the total number of instantiations, not recursion depth
- exceeding the limit raises `input_invalid(kind=instantiation_limit_exceeded)`

## 13. Validation Requirements

At minimum:

- when implementation starts, add template fixtures under `test/fixtures/template/`
- use `ok_*` for normal cases and `ng_*` for invalid cases
- add at least:
  - successful function/class instantiation cases
  - failure cases for `missing_instantiation`, `duplicate_instantiation`, and `unsupported_type_argument`

Normal cases:

- only the types named by `@instantiate(...)` are generated
- generated code compiles and runs

Error cases:

- direct use without `@instantiate(...)` fails
- duplicate instantiation fails with `duplicate_instantiation`
- type mismatch fails with `unsupported_type_argument`
- malformed `# Pytra::if` blocks fail

Cross-language consistency:

- the same `.py` input must resolve to the same `(template, type_args, instantiated_name)` set for all target languages

## 14. Phased Rollout

- Phase 1:
  - frontend can parse `@template` / `@instantiate` and compile-time branch directives
  - implement `explicit` output first
- Phase 2:
  - add native-template output for languages that support it
  - add switching between `native` and `explicit`
- Phase 3:
  - optionally add inference helpers that reduce instantiation boilerplate

## 15. Gap Against Current Implementation (as of 2026-02-22)

- `typing.TypeVar` is annotation-only and template functionality is not implemented.
- The self-hosted parser does not yet interpret template-specific syntax/API.
- This document is a design baseline for future template implementation.

## 16. `.py` Notation (v1 Canonical / Long-Term Extension)

The v1 canonical syntax is **`@template("T", ...)`**.
`@instantiate(...)` remains a long-term extension candidate.

### 16.1 Single-Type-Parameter Function Example

```python
@template("T")
@instantiate("identity_i64", int64)
@instantiate("identity_str", str)
def identity(x: T) -> T:
    return x
```

### 16.2 Two-Type-Parameter Function Example

```python
@template("K", "V")
@instantiate("pair_i64_str", int64, str)
@instantiate("pair_f64_bool", float64, bool)
def pair(key: K, value: V) -> tuple[K, V]:
    return (key, value)
```

### 16.3 Class Example

```python
@template("T")
@instantiate("Box_i64", int64)
@instantiate("Box_str", str)
class Box:
    value: T

    def __init__(self, value: T) -> None:
        self.value = value
```

- Strengths:
  - instantiated definitions stay close to the source definition
  - no extra `as_name` parameter is needed
  - type arguments are explicit and easy to validate statically
- Caveats:
  - many instantiations make the decorator block vertically long
  - string-based names are weaker for IDE rename support
  - if the decorator is ever evaluated at Python runtime, Pytra must define no-op behavior and fixed evaluation rules

## 17. Adopted / Pending / Rejected (2026-02-23)

Adopted:

- `TypeVar` remains annotation-only rather than providing template functionality.
  - moved to: `docs/en/spec/spec-pylib-modules.md`

Pending:

- the main template-body specification in §§1-14
- long-term extensions such as `@instantiate(...)`, compile-time branches, and class generics

Adopted (2026-03-08 update):

- linked runtime helper v1 uses `@template("T", ...)` as the canonical syntax
- v1 is limited to runtime helpers, top-level functions, and no explicit instantiation

Rejected:

- wording that prematurely marks the notation as "adopted" in implementation rather than keeping it as a staged design
