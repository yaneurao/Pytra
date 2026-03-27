<a href="../../../ja/plans/archive/20260317-p1-cpp-subscript-index-cast-tuple-get.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: C++ emitter subscript index cast elision and tuple std::get<I> optimization

Last updated: 2026-03-17

Related TODO:
- `ID: P1-CPP-SUBSCRIPT-IDX-OPT-01` in `docs/ja/todo/index.md` (archived)

Background:
- The C++ emitter wrapped subscript index expressions in `py_to<int64>(...)` unconditionally even when the index had a confirmed `resolved_type` of `int64`, resulting in unnecessary identity casts.
- Tuple constant-index access was confirmed to already emit `::std::get<I>(tup)` via the existing code path (line 3884 of `cpp_emitter.py`); no change needed there.

Purpose:
- Elide `py_to<int64>(...)` wrapping in subscript index generation when the index `resolved_type` is already `int64`.
- Verify that tuple constant-index access correctly emits `::std::get<I>` and add regression tests.

Subtasks:
- [x] S1-01: Audit the current subscript index generation path and classify where `py_to<int64>` remains and whether `resolved_type` is available.
- [x] S1-02: Specify the safety conditions for `::std::get<I>` elision (constant integer index / confirmed tuple element type / no `Any`).
- [x] S2-01: Add `resolved_type == int64` guard to the emitter subscript index generation path and elide the `py_to<int64>` wrap.
- [x] S2-02: Confirm `::std::get<I>` direct emit for tuple constant-index access; verify fallback path is maintained.
- [x] S3-01: Add unit tests fixing the elision boundary (type-confirmed path vs `Any`/`object` fallback) and confirm no regression via transpile check.

Decision log:
- 2026-03-17: Identified during P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01 S2-03 work that `py_to<int64>(int64_expr)` identity casts remained in the emitter inline path since EAST3 `IdentityPyToElisionPass` does not cover the emitter's inline generation. Filed as an independent P1 task.
- 2026-03-17: Implementation complete. Added `idx_as_int64 = idx if idx_ty == "int64" else f"py_to<int64>({idx})"` guard in `_render_subscript_expr` (4 sites) and `render_lvalue` (2 sites). Confirmed `::std::get<I>` emit for tuple constant index is already correct. Added 6 boundary tests, updated 14 existing test expectations, transpile check 145/145 passed, selfhost passed. cpp version 0.576.0 → 0.577.0.
