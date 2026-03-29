<a href="../../../ja/plans/archive/20260312-p1-dataclass-field-static-subset.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: static dataclass `field(...)` subset

Last updated: 2026-03-12

Related TODO:
- `ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01` in `docs/en/todo/index.md`

Background:
- Pytra-NES uses `dataclasses.field(...)` in representative forms such as `timestamps: deque[float] = field(init=False, repr=False)`.
- Current Pytra does not absorb `field(...)` as dataclass metadata and instead forwards it to backends as an ordinary expression or function call.
- As a result, the representative C++ lane emits broken constructor/default code such as `field(false, false)`, which blocks the experiment.
- The required capability here is not reflection or runtime field introspection, but only a compile-time dataclass metadata subset.

Goal:
- Treat `dataclasses.field(...)` as static dataclass metadata rather than a runtime call.
- In v1, formally support the subset `default` / `default_factory` / `init` / `repr` / `compare` and lock representative lanes with explicit backend policy.
- Keep unsupported options fail-closed instead of silently falling back.

In scope:
- Static metadata absorption of `field(...)` during frontend / lowering
- Carrying `default` / `default_factory` / `init` / `repr` / `compare` in the dataclass field carrier
- Representative constructor-generation and field-initialization policy
- Contracts that prevent `field(...)` from appearing in runtime backend output on representative backends
- Fail-closed regressions for unsupported options or unsupported factories

Out of scope:
- Dataclass field reflection or runtime metadata APIs
- Full Python dataclasses parity
- Advanced options such as `metadata`, `hash`, and `kw_only`
- Allowing arbitrary callables as `default_factory`
- Solving full backend support for `deque[T]` as part of this task

Acceptance criteria:
- In representative cases, `field(...)` no longer leaks into backend output as an ordinary expression.
- `init=False` affects constructor generation.
- The v1 subset `default` / `default_factory` / `repr` / `compare` is carried in the field carrier.
- Unsupported options fail closed explicitly.
- `python3 tools/check/check_todo_priority.py`, focused unit tests, `python3 tools/build_selfhost.py`, and `git diff --check` all pass.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k dataclass`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: `field(...)` will be absorbed as a compile-time dataclass metadata subset, not treated as a runtime function. No reflection or dynamic typing will be introduced.
- 2026-03-12: The v1 subset is limited to `default` / `default_factory` / `init` / `repr` / `compare`; everything else remains fail-closed.
- 2026-03-12: `default_factory` will initially focus on representative zero-argument factories; full arbitrary-callable support is deferred.
- 2026-03-12: Full backend support for `deque[T]` is a separate topic, so this task first locks the contract that `field(...)` itself must not leak as an expression.
- 2026-03-12: The representative baseline `timestamps: deque[float] = field(init=False, repr=False)` was confirmed. The initial state kept `field(...)` as a plain `Call(Name("field"))`, and the C++ backend emitted `deque[float64] timestamps;` plus `field(false, false)` as a broken constructor default.
- 2026-03-12: `S2-01` added `core_dataclass_field_semantics.py` and changed class-body `AnnAssign` parsing so representative `field(...)` calls are absorbed into `AnnAssign.meta.dataclass_field_v1` while `value` no longer reaches backend emission. The v1 subset now carries `default` / `default_factory` / `init` / `repr` / `compare` in metadata.
- 2026-03-12: `S2-02` makes the C++ dataclass auto-constructor read `meta.dataclass_field_v1`, omit `init=False` fields from ctor parameters, and use `default` / `default_factory` for representative constructor defaults or member initialization.
- 2026-03-12: `S3-01` locked representative regressions for `repr` / `compare` metadata and the fail-closed policy for unsupported options, duplicate options, and `default` + `default_factory` conflicts. The representative C++ lane is also checked so `field(...)` calls and metadata keys do not leak into output.
- 2026-03-12: `S3-02` split the dataclass field semantics source contract into an independent test and synchronized the helper surface, module parser integration, and docs so the task is ready to close.

## Breakdown

- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S1-01] Lock representative failures and scope with regressions and docs.
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-01] Absorb `field(...)` into a static metadata carrier during frontend / lowering.
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S2-02] Lock constructor / field-init contracts for `init` / `default` / `default_factory`.
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-01] Lock metadata lanes for `repr` / `compare` and the fail-closed policy for unsupported options.
- [x] [ID: P1-DATACLASS-FIELD-STATIC-SUBSET-01-S3-02] Sync docs / TODO / regressions / inventories and close the task.
