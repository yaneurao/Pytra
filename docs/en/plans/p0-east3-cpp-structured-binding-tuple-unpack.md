<a href="../../ja/plans/p0-east3-cpp-structured-binding-tuple-unpack.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Reduce C++ Tuple Unpack to Structured Bindings via EAST3 Markers

Last updated: 2026-03-02

Related TODO:
- `ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01` in `docs/ja/todo/index.md`

Background:
- In `sample/cpp/16_glass_sculpture_chaos.cpp`, tuple-return unpacking is emitted as `auto __tuple_n = call(...);` plus chained `std::get<i>(__tuple_n)`.
- From C++17 onward, structured bindings (`auto [x, y, z] = ...;`) provide an equivalent and more readable form.
- But converting in cases like reassignment, `Any/object` boundaries, or optional/union can introduce semantic differences if done incorrectly.

Goal:
- Mark tuple unpacks in EAST3 when structured binding is safe, and reduce `std::get` chains in the C++ emitter.
- Fall back to the current path (temporary variable + `std::get`) when conditions are not met, preserving fail-closed behavior.

In scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (marker assignment in new/existing passes)
- `src/hooks/cpp/emitter/stmt.py` (tuple assign emission)
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/16_glass_sculpture_chaos.cpp` (regeneration check)

Out of scope:
- Policy changes for tuple targets in `for` loops (`for (auto [a,b] : ...)`)
- Tuple-unpack representation changes in other backends (Rust/Scala/Go, etc.)
- Full rewrite of tuple-value type inference algorithms

Acceptance criteria:
- EAST3 markers are added for `Assign` tuple-unpack cases that satisfy safety conditions.
- C++ emitter outputs `auto [a, b, c] = expr;` for marked cases.
- The following cases keep the current path:
  - Reassignment to existing variables (unpack without declaration)
  - optional/union/Any/object boundaries
  - Element-count mismatch or unpack including `*rest`
- `check_py2cpp_transpile.py` and related unit tests pass, and `sample/cpp/16` confirms reduction of `std::get` chains.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 16_glass_sculpture_chaos --force`

Decision log:
- 2026-03-02: Per user direction, filed P0 to add EAST3 safety-condition markers and reduce to structured bindings in `CppEmitter`.
- 2026-03-02: Extended `TupleTargetDirectExpansionPass`; now `Assign(Tuple)` gets `cpp_struct_bind_unpack_v1` (`version/names/types`) only when `resolved_type == tuple[...]` and element types are not `Any/object/unknown`. Unified fail-closed marker removal for `union`, type mismatch, non-Name elements, and duplicate names.
- 2026-03-02: Added marker-reference path in `CppEmitter.emit_assign`; output `auto [a, b, ...] = expr;` only for declaration-time unpack with matching hints. Reassignment or hint mismatch falls back to existing `auto __tuple_n` + `std::get` path.
- 2026-03-02: Ran verification commands and confirmed major tuple-unpack sites in `sample/cpp/16` were reduced to structured bindings.
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v` (49 tests, OK)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (98 tests, OK)
  - `python3 tools/regenerate_samples.py --langs cpp --stems 16_glass_sculpture_chaos --force` (regen=1 fail=0)
  - `python3 tools/check_py2cpp_transpile.py` (checked=136 ok=136 fail=0 skipped=6)

## Breakdown

- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-01] Specify applicability conditions (declaration-time unpack / fixed tuple elements / non-Any-object).
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-02] Define EAST3 marker schema (for example `cpp_struct_bind_unpack_v1`) and fail-closed conditions.
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-01] Add markers to target `Assign(Tuple)` nodes in an EAST3 optimizer pass.
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-02] Switch CppEmitter tuple-assign branch to marker-driven logic and implement structured-binding output.
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-03] Lock fallback behavior for missing/inconsistent markers and keep the current `std::get` path.
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-01] Add unit tests to lock structured-binding apply/non-apply boundaries.
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-02] Verify no regressions with `sample/cpp/16` regeneration and transpile checks.
