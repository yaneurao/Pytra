<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Infrastructure / Tools / Spec

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-03

## Operating Rules

- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.

For completed tasks, see the [archive](archive/20260403.md).

## Incomplete Tasks

### P0-MAPPING-FQCN-KEY: Unify mapping.json calls keys to fully-qualified names

Context: [docs/ja/plans/p0-mapping-fqcn-key.md](../plans/p0-mapping-fqcn-key.md)

The shared infrastructure `code_emitter.py`'s `resolve_runtime_symbol_name` looks up mapping.json only by `runtime_symbol` (bare `"sin"` etc.), which risks collisions with user-defined functions. Since EAST3 holds fully-qualified `runtime_module_id` + `runtime_symbol`, mapping.json keys should also be fully qualified, like `"pytra.std.math.sin"`.

1. [ ] [ID: P0-FQCN-KEY-S1] Add a `module_id` parameter to `resolve_runtime_symbol_name` and look up by fully-qualified name first
2. [ ] [ID: P0-FQCN-KEY-S2] Unify all language mapping.json keys to fully-qualified names and remove duplicate entries
3. [ ] [ID: P0-FQCN-KEY-S3] Remove the bare fallback
4. [ ] [ID: P0-FQCN-KEY-S4] Update `check_runtime_call_coverage.py` comparisons to use fully-qualified names
5. [ ] [ID: P0-FQCN-KEY-S5] Confirm with representative C++ parity (delegate per-language verification to each owner)

### P10-LEGACY-TOOLCHAIN-REMOVAL: Remove the old toolchain + pytra-cli.py

Context: [docs/ja/plans/p10-legacy-toolchain-removal.md](../plans/p10-legacy-toolchain-removal.md)

**Do not start until the user gives the signal.** Execute at a time when all owners have stopped work.

Targets for removal:
- `src/toolchain/` (old emitter, old compile, old frontends, old misc)
- `src/pytra-cli.py` (old CLI; `src/pytra-cli2.py` is the canonical version)
- References to the old pipeline in tests, specs, and docs

1. [ ] [ID: P10-LEGACY-RM-S1] Delete `src/toolchain/`
2. [ ] [ID: P10-LEGACY-RM-S2] Delete `src/pytra-cli.py` and rename `src/pytra-cli2.py` to `src/pytra-cli.py`
3. [ ] [ID: P10-LEGACY-RM-S3] Update old pipeline references in spec / tutorial / README
4. [ ] [ID: P10-LEGACY-RM-S4] Remove old pipeline references from tools such as `run_local_ci.py`

### P20-DATA-DRIVEN-TESTS: Convert pipeline tests to data-driven format

Context: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

Status: **On hold** — Existing tests are being modified by other agents; begin Phase 1 once things have stabilized.

Of the 267 scripts in `tools/unittest/`, ~80 are pipeline-based (input → parse/resolve/lower/emit → expected output) and can be defined as JSON data. The remaining ~190 (tooling/selfhost/link etc.) stay as Python tests.

**Phase 1: Establish the approach at the emit layer**

1. [ ] [ID: P20-DDT-S1] Create 5–10 JSON test cases in `test/cases/emit/cpp/`
2. [ ] [ID: P20-DDT-S2] Implement `tools/unittest/test_emit_cases.py` (pytest parametrize scanning JSON)
3. [ ] [ID: P20-DDT-S3] Migrate corresponding tests from `test_common_renderer.py` to JSON and delete the original methods

**Phase 2: Extend to the pipeline layer**

4. [ ] [ID: P20-DDT-S4] Create JSON test cases in `test/cases/{east1,east2,east3}/`
5. [ ] [ID: P20-DDT-S5] Implement `tools/unittest/test_pipeline_cases.py`
6. [ ] [ID: P20-DDT-S6] Gradually migrate corresponding tests from `tools/unittest/ir/` and `tools/unittest/toolchain2/` to JSON

**Phase 3: Integrate smoke tests**

7. [ ] [ID: P20-DDT-S7] Migrate `tools/unittest/emit/<lang>/test_py2*_smoke.py` (~20 files) to JSON
8. [ ] [ID: P20-DDT-S8] Migrate `tools/unittest/common/test_pylib_*.py` (~10 files) to JSON
9. [ ] [ID: P20-DDT-S9] Delete scripts that have become empty

### Tasks on Hold

- P20-INT32 is on hold in [plans/p4-int32-default.md](../plans/p4-int32-default.md). Move back here when resuming.
