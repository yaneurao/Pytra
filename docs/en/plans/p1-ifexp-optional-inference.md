<a href="../../ja/plans/p1-ifexp-optional-inference.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-IFEXP-OPTIONAL: Optional type inference for ternary expressions

Last updated: 2026-03-27
Status: Completed

## Background

In the pattern `x = expr if cond else None`, where the true branch has type `T` and the false branch is `None`, `x` should be inferred as `Optional[T]` (= `T | None`). The current resolver cannot perform type inference for this pattern, forcing selfhost code to rewrite ternary expressions as if statements as a workaround.

```python
# Ideally x should be inferred as str | None
x = value_summary["mirror"] if "mirror" in value_summary else None

# Current state: rewriting as if statement because resolver cannot infer
x = ""
if "mirror" in value_summary:
    x = normalize_type_name(value_summary["mirror"])
```

## Design

### Extend IfExp type inference in the resolver

The resolver performs the following for `IfExp` (ternary expression) type inference:

1. Resolve the `resolved_type` of both the true branch (`body`) and false branch (`orelse`)
2. If both branches have the same type, that type becomes the IfExp type (existing behavior)
3. If one branch is `None`, generate `OptionalType(inner=T)` from the other branch's type `T`
4. If both branches have different non-None types, generate a `UnionType`

### Scope of impact

- `IfExp` handling in `src/toolchain2/resolve/py/resolver.py`
- No new EAST nodes needed (only updates to `resolved_type` / `type_expr`)
- No impact on the emitter (it only maps already-narrowed types)

## Subtasks

1. [x] [ID: P1-IFEXP-OPT-S1] Make the resolver's IfExp type inference return `Optional[T]` for `T if cond else None`
2. [x] [ID: P1-IFEXP-OPT-S2] Return `UnionType` when both branches have different non-None types
3. [x] [ID: P1-IFEXP-OPT-S3] Add fixtures + generate golden + confirm parity

## Acceptance Criteria

1. `x = expr if cond else None` infers `x` as `Optional[T]`
2. `x = a if cond else b` (a: int, b: str) infers `x` as `int | str`
3. Existing fixture / sample parity is maintained

## Decision Log

- 2026-03-27: Ternary expressions being rewritten as if statements in go-selfhost. Root cause is that the resolver's IfExp type inference cannot return `Optional[T]`. Filed as a resolver fix.
- 2026-03-27: Added `Optional[T]` / union merge to `IfExp` in the resolver; added `ifexp_optional_inference` fixture, golden, linked, and unit tests. Completed.
