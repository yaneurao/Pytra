# Plan: Data-driven tests for pipeline-level tests (P20-DATA-DRIVEN-TESTS)

## Background

There are 267 test scripts under `tools/unittest/`. Of these, roughly 80 follow the pattern "input: Python source or EAST JSON → run pipeline → verify output string or partial JSON match" — a pattern that does not require Python code.

Target:
- `tools/unittest/ir/` — EAST parser / lowering tests (~30 cases)
- `tools/unittest/toolchain2/` — renderer / narrowing tests (~18 cases)
- `tools/unittest/emit/<lang>/test_py2*_smoke.py` — per-language smoke tests (~20 cases)
- `tools/unittest/common/test_pylib_*.py` — pylib tests (~10 cases)

Out of scope (remain as Python tests):
- `tools/unittest/tooling/` (92 cases) — CLI contract tests, file layout verification, manifest validation. These verify filesystem state or process execution and do not fit the input→output pattern
- `tools/unittest/selfhost/` (12 cases) — selfhost builds, golden comparison, stage2 diff. Primarily process execution and file comparison
- `tools/unittest/link/` (5 cases) — linker graph analysis, export resolution. Test relationships between multiple modules
- Parts of `tools/unittest/common/` — backend registry metadata consistency, runtime symbol index structure validation

Per-language smoke test scripts are prohibited by spec-emitter-guide §13, but the same problem is occurring as method proliferation in `test_common_renderer.py` and script proliferation in `tools/unittest/emit/<lang>/`.

## Design

### Directory Structure

```
test/cases/
  east1/                    # parse tests
    for_range_normalization.json
    range_expr_lowering.json
  east2/                    # resolve tests
    type_inference_int.json
    isinstance_narrowing.json
  east3/                    # lowering tests
    closure_def_capture.json
    block_scope_hoist.json
  emit/                     # emitter tests
    cpp/
      binop_precedence.json
      literal_no_wrap.json
    go/
      container_wrapper.json
    rs/
      trait_dispatch.json
```

### JSON Test Case Format

#### Pipeline tests (east1/east2/east3)

```json
{
  "description": "isinstance narrowing resolves dict type in if block",
  "pipeline": "source_to_east3",
  "input": "def f(x: object) -> str:\n  if isinstance(x, str):\n    return x\n  return ''",
  "assertions": [
    {"path": "body[0].body[0].body[0].value.resolved_type", "equals": "str"},
    {"path": "body[0].body[0].test.resolved_type", "equals": "bool"}
  ]
}
```

`pipeline` values:
- `source_to_east1`: parse only
- `source_to_east2`: parse + resolve
- `source_to_east3`: parse + resolve + lower
- `east3_to_linked`: through linking

`assertions` format:
- `{"path": "json.path.expr", "equals": "value"}` — exact match
- `{"path": "json.path.expr", "contains": "substring"}` — substring match
- `{"path": "json.path.expr", "not_equals": "value"}` — mismatch
- `{"path": "json.path.expr", "exists": true}` — existence check

#### Emitter tests (emit/)

```json
{
  "description": "nested binop respects precedence",
  "target": "cpp",
  "level": "expr",
  "input": {
    "kind": "BinOp",
    "left": {
      "kind": "BinOp",
      "left": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
      "op": "Add",
      "right": {"kind": "Constant", "value": 2, "resolved_type": "int64"},
      "resolved_type": "int64"
    },
    "op": "Mult",
    "right": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
    "resolved_type": "int64"
  },
  "expected": "(int64(1) + int64(2)) * int64(3)"
}
```

`level` values:
- `expr`: expression-level emit (e.g. `emit_cpp_expr`)
- `stmt`: statement-level emit
- `module`: source string → emit (end-to-end)

For `module` level:

```json
{
  "description": "for range emits C++ for loop",
  "target": "cpp",
  "level": "module",
  "input": "def f() -> None:\n  for i in range(10):\n    print(i)",
  "expected_contains": ["for (int64 i = 0; i < 10;", "py_print(i)"]
}
```

### Test Runners

Only **2** test runners:

1. `tools/unittest/test_pipeline_cases.py` — scans `test/cases/{east1,east2,east3}/`
2. `tools/unittest/test_emit_cases.py` — scans `test/cases/emit/<lang>/`

Both use `pytest.mark.parametrize` to dynamically collect JSON files. Adding a case only requires placing a JSON file.

### What remains as Python tests (~190 cases)

The following are difficult to express in JSON and remain as Python tests in `tools/unittest/`:

- `tools/unittest/tooling/` — CLI contracts, file layout, manifest validation (92 cases)
- `tools/unittest/selfhost/` — selfhost builds, golden comparison (12 cases)
- `tools/unittest/link/` — linker graph analysis, export resolution (5 cases)
- Structure-validation cases in `tools/unittest/common/` — backend registry, runtime symbol index, etc.
- Tests that need EmitContext customization
- Multi-file import resolution tests

## Migration Plan

### Phase 1: Establish the pattern in the emit layer

1. Create 5–10 JSON test cases in `test/cases/emit/cpp/`
2. Implement `tools/unittest/test_emit_cases.py`
3. Migrate corresponding tests from `test_common_renderer.py` to JSON and delete the original methods
4. Verify behavior

### Phase 2: Roll out to the pipeline layer

1. Create JSON test cases in `test/cases/{east1,east2,east3}/` (isinstance narrowing, closure capture, etc.)
2. Implement `tools/unittest/test_pipeline_cases.py`
3. Gradually migrate corresponding tests from `tools/unittest/ir/` and `tools/unittest/toolchain2/` to JSON

### Phase 3: Consolidate smoke tests

1. Migrate `tools/unittest/emit/<lang>/test_py2*_smoke.py` (~20 cases) to module-level JSON in `test/cases/emit/<lang>/`
2. Migrate `tools/unittest/common/test_pylib_*.py` (~10 cases) to `test/cases/east2/` or `east3/`
3. Delete scripts that are now empty

### State after Phase 3 is complete

```
test/cases/           # ~80 JSON test cases (data-driven)
  east1/
  east2/
  east3/
  emit/{cpp,go,rs,...}/

tools/unittest/       # ~190 Python tests (remaining)
  test_emit_cases.py      # JSON test runner (emit)
  test_pipeline_cases.py  # JSON test runner (pipeline)
  tooling/                # CLI/manifest contract tests (remaining)
  selfhost/               # selfhost tests (remaining)
  link/                   # linker tests (remaining)
  common/                 # structure validation (remaining)
  emit/cpp/               # only tests needing EmitContext customization remain
  ir/                     # only complex tests that cannot be migrated to JSON remain
```

## Benefits

- Adding pipeline-layer test cases (~80) requires only a JSON file — no Python code changes
- Test cases are easy to survey at a glance (file names describe content)
- The same mechanism works across languages (smoke tests for 20 cases consolidated into JSON)
- Agents adding tests do not need to read existing scripts
- Tooling/CI tests (~190 cases) remain as Python tests without forcing JSON conversion

## Status

On hold. Existing tests are being modified by other agents; Phase 1 will begin once things are stable.
