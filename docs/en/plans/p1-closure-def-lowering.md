<a href="../../ja/plans/p1-closure-def-lowering.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-CLOSURE-DEF: ClosureDef lowering for nested FunctionDef

Last updated: 2026-03-26
Status: Not started

## Background

Python's nested FunctionDef (functions inside functions) cannot be expressed directly in some target languages such as Go. Currently there are cases where the emitter handles this transformation, but analyzing variable captures from outer scopes is a semantic decision and is not within the emitter's responsibility (which is purely mapping notation).

By performing captures analysis in EAST3 and lowering to a `ClosureDef` node (or attaching closure metadata to FunctionDef), each emitter only needs to map to the closure syntax of its target language.

## Design Decisions

### Language classification by level

| Level | Language examples | nested function | closure |
|---|---|---|---|
| A: Native support | JS, TS, Rust, Swift, Kotlin | as-is | as-is |
| B: Has closures | Go, C++, Java, C# | convert to closure | as-is |

All current target languages fall into level A or B. Languages without closures (e.g. C) are not currently a backend, so support is deferred (YAGNI).

### Separation of concerns

- **EAST3 common**: detect nested FunctionDef, lower to `ClosureDef` with capture analysis results attached
- **emitter**: only maps `ClosureDef` to the closure syntax of each language

### Contents of capture analysis

1. Enumerate variables from outer scopes referenced by the nested FunctionDef
2. Determine capture mode (`readonly` / `mutable`)
3. Store as a `captures` list on the ClosureDef node

```json
{
  "kind": "ClosureDef",
  "name": "inner",
  "captures": [
    {"name": "x", "mode": "readonly", "type_expr": ...},
    {"name": "y", "mode": "mutable", "type_expr": ...}
  ],
  "args": [...],
  "body": [...],
  "return_type_expr": ...
}
```

### Integration with LifetimeAnalysisPass

The existing `LifetimeAnalysisPass` (def-use analysis + liveness information) can serve as the foundation for capture analysis. Which variables in outer scopes a nested function references can be derived from def-use information.

### Emitter mapping targets

| Language | Mapping target |
|---|---|
| Go | `inner := func(...) { ... }` |
| C++ | `auto inner = [&x, y](...) { ... };` (readonly by value, mutable by reference) |
| Java | lambda or anonymous class |
| C# | lambda |
| JS/TS | nested function as-is (level A) |
| Rust | `let inner = \|...\| { ... };` |
| Swift | `let inner = { (...) -> T in ... }` |
| Kotlin | `val inner = { ... -> ... }` |

For level A languages, `ClosureDef` may be output as a normal nested function.

## Risks

- Cases where a nested function recursively calls itself (requires named closure)
- Go constraints on mutable capture (Go always captures by reference, but no explicit annotation needed)
- Correct determination of C++ capture mode (`[=]` / `[&]` / per-variable specification)

## Subtasks

1. [ID: P1-CLOSURE-DEF-S1] Add ClosureDef node specification to spec-east.md for EAST3
2. [ID: P1-CLOSURE-DEF-S2] Implement capture analysis + ClosureDef generation in EAST3 lowering
3. [ID: P1-CLOSURE-DEF-S3] Add fixtures (capture patterns for nested functions) + generate golden
4. [ID: P1-CLOSURE-DEF-S4] Implement ClosureDef mapping in each emitter + confirm parity

## Acceptance Criteria

1. Nested FunctionDef is lowered to `ClosureDef` in EAST3
2. The captures list correctly enumerates captured variables and their modes
3. Existing fixture + sample parity is maintained
4. No capture analysis logic exists in the emitter

## Decision Log

- 2026-03-26: Decided that transformation of nested FunctionDef is the responsibility of EAST3 lowering, not the emitter. Since all current target languages support closures, support for closure-less languages (function extraction + struct pattern) is deferred as YAGNI.
