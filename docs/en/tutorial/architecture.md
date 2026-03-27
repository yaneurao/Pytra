<a href="../../ja/tutorial/architecture.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Pytra Architecture

Pytra is a transpiler that converts a subset of Python into multiple target languages.
This page provides an overview of the pipeline and the role of each stage.

## Pipeline Overview

```
  .py source
      │
      ▼
  ┌─────────┐
  │  parse   │  Python syntax analysis
  └────┬─────┘
       │  .py.east1 (Python-specific intermediate representation)
       ▼
  ┌─────────┐
  │ resolve  │  Type resolution + syntax normalization
  └────┬─────┘
       │  .east2 (language-independent intermediate representation)
       ▼
  ┌─────────┐
  │ compile  │  Core lowering (instruction generation)
  └────┬─────┘
       │  .east3 (pre-optimization instructioned IR)
       ▼
  ┌──────────┐
  │ optimize │  Whole-program optimization
  └────┬─────┘
       │  .east3 (optimized IR)
       ▼
  ┌─────────┐
  │  link    │  Multi-module linking
  └────┬─────┘
       │  manifest.json + linked east3 modules
       ▼
  ┌─────────┐
  │  emit    │  Target code generation
  └────┬─────┘
       │
       ▼
  .go / .cpp / .rs / ...
```

## Role of Each Stage

### parse (syntax analysis)

```
Input:  .py file
Output: .py.east1 (JSON)
```

Reads Python source code and produces EAST1 (Extended AST, Stage 1).

- Syntax analysis only. No type resolution.
- Type annotations are preserved as written in the source (`int` stays `int`, not yet `int64`).
- Source locations (line/column numbers), comments, and blank lines are preserved.
- Each module is completely independent — no other files are referenced.
- The `.py.east1` extension indicates "EAST1 derived from Python."

### resolve (type resolution + syntax normalization)

```
Input:  *.py.east1 (multiple modules)
Output: *.east2 (JSON)
```

Takes EAST1, performs type resolution and Python-specific syntax normalization, and produces language-independent EAST2.

- **Type resolution**: All expressions have their types determined. For example, `math.sqrt()` returns `float64`.
- **Type annotation normalization**: Python type names are converted to canonical types.
  - `int` → `int64`, `float` → `float64`, `bytes` → `list[uint8]`, etc.
- **Syntax normalization**: Python-specific syntax is converted to language-independent representations.
  - `for x in range(n)` → `ForRange` node
  - `Optional[X]` → `X | None`
- **Cast insertion**: Automatic conversions are inserted where types mismatch.
  - Example: `math.sqrt(int_var)` → an `int64 → float64` cast is inserted for the argument
- **Cross-module type resolution**: Function signatures from imported modules are referenced to resolve types.
  - Built-ins like `len`, `print` from `built_in.py` are resolved the same way (no hardcoding).
- The `.py` disappears from the extension, becoming `.east2`, indicating "Python semantics have been removed."

### compile (core lowering)

```
Input:  *.east2
Output: *.east3 (JSON)
```

Takes EAST2 and performs backend-independent instruction generation, producing EAST3.

- **Boxing/unboxing**: Polymorphic value passing is made into explicit instructions.
- **type_id checks**: `isinstance` is converted to efficient type ID comparisons.
- **Iteration plans**: `for` loops are converted to `ForCore` + `iter_plan`.
- **dispatch_mode application**: The compilation strategy (`native` / `type_id`) is reflected in EAST3.
  This application happens only once during EAST2 → EAST3 and is not re-evaluated later.

### optimize (whole-program optimization)

```
Input:  *.east3
Output: *.east3 (optimized, JSON)
```

Applies language-independent optimization passes to EAST3.

- Removal of unnecessary casts
- Literal folding
- Dead code elimination
- Loop optimization
- Escape analysis
- Other local optimizations

Optimization is optional — correct code is generated even if it is skipped.

### link (multi-module linking)

```
Input:  *.east3 (optimized)
Output: manifest.json + linked east3 modules
```

Links multiple EAST3 modules and gathers the information needed for emit.

- **Import graph resolution**: Collects all modules that the user code depends on.
- **Runtime module addition**: Adds runtime EAST3 such as `built_in/io_ops`, `std/time`, `utils/png`.
- **manifest.json generation**: Produces a manifest describing entry modules, module list, and output paths.
- **type_id table generation**: Finalizes the type ID table for class inheritance checks.
- **linked_program_v1 metadata**: Attaches whole-program information to each module's meta.

### emit (code generation)

```
Input:  *.east3 (optimized)
Output: .go / .cpp / .rs / .js, etc.
```

Takes EAST3 and generates target language source code.

- Simply maps EAST3 nodes to target language syntax. No re-interpretation of semantics.
- Also handles runtime library placement and import/include generation.
- Each language has an independent emitter (`emit/go/`, `emit/cpp/`, etc.).

## What is EAST?

EAST (Extended AST) is Pytra's intermediate representation, expressed in JSON format.

Unlike the abstract syntax tree provided by Python's standard `ast` module, EAST:

- **Preserves comments and blank lines** — faithfully reflects source code structure.
- **Preserves type information** — attaches resolved type annotations to all nodes.
- **Language-independent** — from EAST2 onward, no Python-specific information is included.
- **Information is determined incrementally** — progresses from EAST1 (unresolved) → EAST2 (types determined) → EAST3 (instructioned).

| Stage | File extension | Type state | Language dependency |
|---|---|---|---|
| EAST1 | `.py.east1` | Unresolved | Python-specific |
| EAST2 | `.east2` | Determined | Language-independent |
| EAST3 | `.east3` | Determined + instructioned | Language-independent |

## CLI Commands

Normally you use `./pytra` for a single command, but you can also run each stage individually.

```bash
# All-in-one (normal usage)
./pytra input.py --target cpp --output-dir out/

# Individual stages (for debugging / investigation)
pytra-cli2 -parse input.py -o input.py.east1
pytra-cli2 -resolve input.py.east1 -o input.east2
pytra-cli2 -compile input.east2 -o input.east3
pytra-cli2 -optimize input.east3 -o input.east3
pytra-cli2 -link input.east3 -o out/
pytra-cli2 -emit --target=cpp out/manifest.json -o out/emit/
```

## Supported Languages

Pytra supports transpilation to the following languages:

C++, Rust, C#, JavaScript, TypeScript, Go, Java, Kotlin, Swift, Ruby, Lua, Scala, PHP, Nim, Dart, Julia, Zig

## Related Documentation

- [How to use](./how-to-use.md) — Execution steps, options
- [Python compatibility guide](../spec/spec-python-compat.md) — Unsupported syntax, differences from Python
- [EAST2 specification](../spec/spec-east2.md) — The resolve output contract
- [Specification index](../spec/index.md) — Entry point for all specifications
