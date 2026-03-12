# P0: homogeneous tuple ellipsis support

Last updated: 2026-03-12

Related TODO:
- `ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01` in `docs/en/todo/index.md`

Background:
- A representative Pytra-NES case uses homogeneous variadic tuples such as `LENGTH_TABLE: tuple[int, ...] = (...)`.
- The current C++ backend treats `tuple[int, ...]` like a fixed tuple and emits invalid C++ such as `::std::tuple<int64, ...>`.
- `tuple[T, ...]` has different semantics from fixed-arity tuples like `tuple[int, str]`, so the type system and backend lowering need a distinct category.
- For v1, the realistic target is not full immutable-tuple parity, but a practical `homogeneous immutable sequence` lane that covers representative use cases first.

Goal:
- Accept `tuple[T, ...]` as a first-class input type in Pytra and distinguish it from fixed tuples.
- In v1, treat `tuple[T, ...]` as a mutation-forbidden homogeneous immutable sequence and make representative constant / local / argument / return lanes work on major backends.
- Keep unsupported backends or unsupported lanes fail-closed so invalid code generation stops immediately.

In scope:
- Recognition of `tuple[T, ...]` in type parsing and normalization
- Separate category handling in EAST / EAST3 / type summaries
- Fixing the current invalid C++ emission of `::std::tuple<int64, ...>`
- Homogeneous variadic tuple lowering on representative backends
- Fail-closed contracts, regressions, and documentation

Out of scope:
- Redesign of fixed tuples (`tuple[int, str]`)
- Full Python parity for tuple equality / hashing / slicing / concatenation
- Early optimization for arbitrary nested tuple structures
- Full unification of tuple and list APIs

Acceptance criteria:
- A representative fixture containing `tuple[int, ...]` is accepted by the frontend.
- The C++ backend no longer emits invalid types such as `::std::tuple<int64, ...>`.
- The representative v1 lanes (constants, locals, function args, returns, read-only index access) emit according to target policy.
- Unsupported backends or lanes fail closed instead of silently falling back.
- `python3 tools/check_todo_priority.py`, focused unit tests, `python3 tools/build_selfhost.py`, and `git diff --check` all pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k tuple`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: `tuple[T, ...]` will not share the same lane as fixed tuples. In v1 it is split out as a `homogeneous immutable sequence` category because the current C++ emission produces invalid `::std::tuple<int64, ...>`.
- 2026-03-12: v1 will lock representative lanes first and prefer fail-closed behavior for unsupported backends or lanes. Whether all backends should eventually reuse the exact same representation as lists is deferred.
- 2026-03-12: The current parser does not reject `tuple[int, ...]`; it accepts it as `GenericType(base="tuple", args=[NamedType("int64"), NamedType("...")])`. This baseline and the current invalid C++ emission `::std::tuple<int64, ...>` are now locked by regression before category splitting starts.
- 2026-03-12: `tuple[T, ...]` stays a `GenericType(base="tuple", tuple_shape="homogeneous_ellipsis")` instead of introducing a brand-new TypeExpr kind. The summary layer alone moves it to `category=homogeneous_tuple`, which keeps backend TypeExpr allowlists stable while still separating it from fixed tuples.

## Breakdown

- [x] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S1-01] Lock the type parser / normalization / representative failure with plan and regressions.
- [x] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S2-01] Carry `tuple[T, ...]` as a distinct category from fixed tuples in EAST / type summaries.
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S2-02] Stop invalid C++ emission of `::std::tuple<int64, ...>` and lower the representative v1 lane as a read-only immutable sequence.
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S3-01] Define representative backend policy and lock unsupported lanes / backends as fail-closed.
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S3-02] Sync docs / TODO / regressions / inventories to the current contract and close the task.
