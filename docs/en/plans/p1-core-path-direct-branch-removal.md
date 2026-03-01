# P1: Remove direct `Path` branches from `core.py`

Last updated: 2026-03-01

Related TODO:
- `ID: P1-CORE-PATH-SOT-01` in `docs/ja/todo/index.md`

Background:
- `src/pytra/compiler/east_parts/core.py` still has direct branches dependent on specific standard-library names, such as `fn_name == "Path"`.
- For `Path`, the source of truth is on the `pytra/std/pathlib.py` side. Keeping equivalent knowledge duplicated in compiler side causes follow-up omissions.
- `P0-STDLIB-SOT` is progressing fixes for `perf_counter`, but `Path` branches remain, so this is managed as an additional plan.

Goal:
- Remove direct string-hardcoded return-type inference and BuiltinCall judgment branches for `Path` from `core.py`.
- Unify `Path` resolution through stdlib reference layer (signature/attribute info) and import-resolution info.

In scope:
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/compiler/stdlib/signature_registry.py` (if needed)
- `test/unit/test_east_core.py` (regression)

Out of scope:
- Changing `Path` API spec
- Large backend emitter refactors

Acceptance criteria:
- Direct `Path` branches such as `fn_name == "Path"` are removed from `core.py`.
- For both `from pathlib import Path` and `from pytra.std.pathlib import Path`, return-type inference and BuiltinCall lowering for `Path(...)` are preserved.
- Existing regressions (`test_east_core.py`, `check_py2cpp_transpile.py`) pass without regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east_core.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

## Breakdown

- [x] [ID: P1-CORE-PATH-SOT-01] Remove direct `Path` branches in `core.py` and unify through stdlib reference layer + import-resolution info.
- [x] [ID: P1-CORE-PATH-SOT-01-S1-01] Inventory `Path`-dependent branches in `core.py` (return-type inference / BuiltinCall lower / attribute inference) and pin replacement APIs.
- [x] [ID: P1-CORE-PATH-SOT-01-S2-01] Replace `Path` judgment from direct-name hardcoding to resolver path and remove `fn_name == "Path"` from `core.py`.
- [x] [ID: P1-CORE-PATH-SOT-01-S2-02] Fill return-type inference for `Path` constructor / method / attribute in stdlib reference layer and avoid expanding duplicate compiler-side knowledge in `core.py`.
- [x] [ID: P1-CORE-PATH-SOT-01-S3-01] Add anti-reintroduction regressions in `test_east_core.py` so direct-`Path` reintroduction is detectable.
- [x] [ID: P1-CORE-PATH-SOT-01-S3-02] Run `check_py2cpp_transpile.py` and confirm no regression.

## S1-01 Inventory results (direct `Path` dependencies in `core.py`)

### 1. Locations of direct `Path` branches

- `src/pytra/compiler/east_parts/core.py:2437`
  - In return-type inference for `Call(Name)`, `elif fn_name == "Path": call_ret = "Path"`.
- `src/pytra/compiler/east_parts/core.py:2489`
  - In return-type inference for `Call(Attribute)`, `if owner_t == "Path": ...` (`read_text/name/stem/exists/mkdir/write_text`).
- `src/pytra/compiler/east_parts/core.py:2561`
  - In BuiltinCall lowering, `elif fn_name == "Path": runtime_call = "Path"`.
- `src/pytra/compiler/east_parts/core.py:2918`
  - In type inference for `BinOp "/"`, returns `Path` via direct compare `lt == "Path"`.

### 2. Existing stdlib reference APIs (reusable)

- `lookup_stdlib_function_return_type(fn_name)`
- `lookup_stdlib_function_runtime_call(fn_name)`
- `lookup_stdlib_method_runtime_call(owner_t, attr)`
- `lookup_stdlib_attribute_type(owner_t, attr)`
- Note: `lookup_stdlib_method_return_type(owner_t, method)` exists in `signature_registry.py` but is not used in `core.py`.

### 3. Replacement policy (for S2 implementation)

- Constructor judgment:
  - Remove direct comparison `fn_name == "Path"`; add resolver that judges whether symbol is `pathlib.Path` via import-resolution info (`meta.import_symbols`).
- Return-type inference:
  - Use `lookup_stdlib_method_return_type("Path", method)` as primary source for `Path` method return types, without `core.py`-specific dictionaries.
- BuiltinCall lowering:
  - Add `runtime_call="Path"` only when resolver judgment passes for `Path` constructor.
- `BinOp "/"`:
  - Replace `Path`-specific operation with judgment "lhs resolved as stdlib `Path`" and remove direct `lt == "Path"` comparison.

Decision log:
- 2026-03-01: Per user instruction, started managing the policy to remove direct `Path` branches from `core.py` under `P1`.
- 2026-03-01: Inventoried 4 direct `Path` dependencies in `core.py` (2 return-type inference, 1 BuiltinCall, 1 operation-type inference) and reusable stdlib APIs, and finalized S2 replacement policy (`S1-01`).
- 2026-03-01: Removed direct branches `fn_name == "Path"` / `owner_t == "Path"` in `core.py`, and moved to resolver via `lookup_stdlib_imported_symbol_return_type` / `lookup_stdlib_imported_symbol_runtime_call` (`P1-CORE-PATH-SOT-01-S2-01`).
- 2026-03-01: Moved `Path` method return-type inference to `lookup_stdlib_method_return_type`, and verified constructor inference and `BuiltinCall(runtime_call=Path)` retention for `from pathlib import Path as P` / `from pytra.std.pathlib import Path as PP` in `test_east_core.py` (`P1-CORE-PATH-SOT-01-S2-02`).
- 2026-03-01: Added anti-reintroduction detection for direct `Path` branches and alias-import regressions to `test_east_core.py`, and passed `python3 -m unittest discover -s test/unit -p 'test_east_core.py' -v` (28 cases) (`P1-CORE-PATH-SOT-01-S3-01`).
- 2026-03-01: Ran `python3 tools/check_py2cpp_transpile.py` and confirmed no regression with `checked=134 ok=134 fail=0 skipped=6` (`P1-CORE-PATH-SOT-01-S3-02`).
