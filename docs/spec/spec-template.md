<a href="../../docs-ja/spec/spec-template.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Template Specification (Draft)

This document defines the generic/template support policy in Pytra.
In particular, it treats **template definition + explicit instantiation** written directly in `.py` as the canonical workflow.

## 1. Objectives

- Enable defining generic functions/classes on the Python side and safely transpiling them to multiple languages including C++.
- Reduce fallback to `object` and preserve static typing in generated code.
- Generate concretized code even for languages with weak or constrained template support.

## 2. Non-goals

- Full reproduction of all Python typing-system (`typing`) features.
- Full compatibility with higher-kinded types / partial specialization / metaprogramming.
- Reproducing dynamic dispatch that depends on runtime type erasure.

## 3. Core policy

- Hold generic intermediate representation in EAST.
- For languages with weak template support, use monomorphization (explicit instantiation).
- Concretization follows "explicitly generate only the used types"; no implicit exhaustive search.
- Calling template bodies directly is disallowed; call concretized symbols only.

## 4. Terms

- Template definition: a function/class definition with type parameters.
- Instantiation: binding concrete type arguments and generating concrete code.
- Instantiated symbol: the concrete symbol used for calls/construction after instantiation.

## 5. `.py` notation

### 5.1 Basic API

- Add `pytra.std.template` and provide decorators:
  - `@template("T", "U", ...)`
  - `@instantiate("instantiated_name", type_arg1, type_arg2, ...)`
- `@template` applies only to the immediately following single `def`/`class`.
  - It does not continue until next `def`/`class`.
  - It does not affect the whole module.
- `@instantiate` is written in the same decorator block, directly above the target definition.

### 5.2 Template function definition

```python
from pytra.std.template import template, instantiate

@template("T")
@instantiate("add_i64", int64)
@instantiate("add_f64", float64)
def add(a: T, b: T) -> T:
    return a + b
```

### 5.3 Template class definition

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

### 5.4 Usage rules

- Calls/construction must use symbols declared via `@instantiate`.
- Direct template-body usage such as `add(...)` or `Vec2(...)` is forbidden (`explicit` policy).
- First argument of `@instantiate("name", ...)` is treated as the generated instantiated symbol name.

### 5.5 Compile-time branch directives

Inside template bodies, use these directives for compile-time branching:

```python
# Pytra::if T == int64
...
# Pytra::elif T == str
...
# Pytra::else
...
# Pytra::endif
```

- Use `# Pytra::if` / `# Pytra::elif` / `# Pytra::else` / `# Pytra::endif` as one block.
- Left operand can be only template type parameters (`T`, `K`, `V`, etc.).
- Allowed comparisons in v1: `==` / `!=` only.
- Right operand uses type tokens (`int64`, `str`, `float64`, etc.).
  - Quoted forms like `# Pytra::if T == "int64"` may be accepted for compatibility, but unquoted form is canonical.
- Evaluate per `@instantiate` and keep only the selected branch.

## 6. Syntax constraints

- `@template` / `@instantiate` are allowed only on module-top-level `def` / `class`.
- `@template("...")` arguments must be string-literal identifiers.
- First argument of `@instantiate("name", ...)` must be a string-literal identifier.
- Number of `@instantiate` type arguments must match number of `@template` type parameters.
- `# Pytra::if` directives are allowed only inside template bodies.
- Nesting of `# Pytra::if` directives is disallowed in v1.

## 7. Resolution rules

- Instantiated symbol is fixed by `@instantiate("name", type_args...)`.
- Duplicate `name` within a single template definition: `input_invalid(kind=symbol_collision)`.
- Duplicate type-argument tuple within a single template definition: `input_invalid(kind=duplicate_instantiation)`.
- Direct call to template body: `input_invalid(kind=missing_instantiation)`.
- Resolve compile-time directives per instantiation into one block before regular transpilation.

## 8. Name generation (mangling)

- Instantiated symbols are converted to unique names that include type arguments.
- Recommended format:
  - `__pytra__<module>__<symbol>__<type1>__...`
- Character encoding rule:
  - Replace non-`[A-Za-z0-9_]` with `_xx` (two-digit hex).
- Name collision: `input_invalid(kind=symbol_collision)`.

## 9. Target-language output policy

- Languages with strong native templates (C++/Rust, etc.):
  - support selectable `native` output or `explicit` output.
- Languages without template support or with strong constraints:
  - use `explicit` output as default.
- In all languages, `.py`-side `@instantiate(...)` is canonical; do not depend on external definition files.

## 10. Type constraints

- Do not allow implicit degradation to `Any` / `object` inside template bodies.
- Allowed type arguments are restricted to EAST canonical types (`int64`, `float64`, `str`, `list[T]`, etc.).
- If unknown/unresolved types remain, stop with `inference_failure`.

## 11. Error contract

Use the following for template-related failures:

- `input_invalid(kind=missing_instantiation)`
- `input_invalid(kind=duplicate_instantiation)`
- `input_invalid(kind=symbol_collision)`
- `input_invalid(kind=unsupported_type_argument)`
- `input_invalid(kind=invalid_instantiation_form)`
- `input_invalid(kind=invalid_compile_time_branch)`
- `input_invalid(kind=unmatched_compile_time_branch)`
- `input_invalid(kind=unbound_template_param)`
- `unsupported_syntax` (unsupported notation)

Error details must include at least `module`, `symbol`, `type_args`, and `source_span`.

## 12. Generation-volume guard

To prevent instantiation explosion, provide:

- `--max-instantiations N` (with default)
  - Upper bound for total instantiated symbols generated in one transpile run.
  - Includes both directly specified and transitively generated instantiations.
  - This is not a recursion-depth limit.
- If total exceeds `N`, stop with `input_invalid(kind=instantiation_limit_exceeded)`.

## 13. Validation requirements

At minimum, pass:

- Normal cases:
  - Only types specified in `.py` `@instantiate(...)` are generated.
  - Generated code compiles/runs.
- Error cases:
  - Direct call without `@instantiate(...)` fails.
  - Duplicate instantiation fails with `duplicate_instantiation`.
  - Type mismatch fails with `unsupported_type_argument`.
  - Compile-time directive mismatch (for example missing `endif`) fails.
- Cross-language consistency:
  - Same `.py` input yields identical resolution results across targets (template/type_args/instantiated_name).

## 14. Phased rollout

- Phase 1:
  - Frontend can parse `.py` `@template` / `@instantiate` and `# Pytra::if`.
  - Implement `explicit` output first.
- Phase 2:
  - Introduce direct template output in languages supporting `native` output.
  - Add switching between `native` and `explicit`.
- Phase 3:
  - Add optional inference assistance (to reduce explicit-instantiation boilerplate) if needed.

## 15. Gap against current implementation (as of 2026-02-22)

- `pytra.std.typing.TypeVar` is a runtime shim (minimal `str` return) and does not provide full type-parameter functionality.
- The self-hosted parser does not yet implement template-specific syntax/API interpretation.
- This specification is treated as the design baseline for upcoming template implementation.

## 16. Adopted `.py` notation

Adopted form is **stacked decorators (identifier arguments)**.

### 16.1 Single-type-parameter function example

```python
@template("T")
@instantiate("identity_i64", int64)
@instantiate("identity_str", str)
def identity(x: T) -> T:
    return x
```

### 16.2 Two-type-parameter function example

```python
@template("K", "V")
@instantiate("pair_i64_str", int64, str)
@instantiate("pair_f64_bool", float64, bool)
def pair(key: K, value: V) -> tuple[K, V]:
    return (key, value)
```

### 16.3 Class example

```python
@template("T")
@instantiate("Box_i64", int64)
@instantiate("Box_str", str)
class Box:
    value: T

    def __init__(self, value: T) -> None:
        self.value = value
```

- Advantages:
  - Instantiation definitions stay close to the function/class definition, making missing instantiations easier to detect.
  - No separate `as_name` argument; instantiated name is short and explicit as first argument.
  - Type arguments are explicit in each instantiation line, making static validation easier to implement.
- Caveats:
  - Functions with many instantiations become vertically long.
  - Instantiated names are string literals, so IDE refactor support is weaker.
  - Since decorators are parsed by Python runtime too, Pytra-specific no-op behavior and evaluation-order specification need to be fixed explicitly.
