<a href="../../../ja/spec/archive/20260328-spec-lua-native-backend.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Lua Native Backend Contract Specification

This document defines the contract for the `EAST3 -> Lua native emitter` path introduced in `P0-LUA-BACKEND-01`.
It covers the responsibilities of the input EAST3, fail-closed behavior on unsupported input, the runtime boundary, and what is out of scope.

## 1. Purpose

- Fix the responsibility boundary for implementing the Lua backend as a direct native generator with no sidecar dependency.
- Document the supported scope and failure conditions on unsupported input, even at the initial implementation stage.
- Prevent the practice of hiding inconsistencies via implicit fallback (escape to another language's backend).

## 2. Input EAST3 Node Responsibilities

The Lua native emitter accepts only EAST3 documents satisfying the following.

- Root is a `dict` with `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is a sequence of EAST3 statement nodes.

Stage responsibilities:

- S1 (skeleton): Minimum path for `Module` / `FunctionDef` / `If` / `ForCore`.
- S2 (body): Minimum set of assignment, arithmetic, comparison, loops, calls, and built-ins.
- S3 (operational): Incrementally add class/instance/isinstance/import and `math` / image runtime.

## 3. Fail-Closed Contract

On receiving unsupported input, fail immediately without escaping to a compatibility path.

- Raise `RuntimeError` the moment an unsupported `kind` / shape is detected.
- The error message must include at least `lang=lua` and the failure kind (node/shape).
- The CLI must exit non-zero and must not treat incomplete `.lua` output as a success.
- Must not implicitly fall back to `py2js` / sidecar / EAST2 compatibility.

## 4. Runtime Boundary

The runtime boundary for Lua-generated code is limited in principle to the following.

- The Lua runtime API under `src/runtime/lua/{generated,native}/` (no `src/runtime/lua/pytra/**` exists in the checked-in repo tree)
- The Lua standard library (`math` / `string` / `table`, etc.)

Prohibitions:

- Node.js sidecar bridge dependencies
- JS runtime shim prerequisites (`pytra/runtime.js`)
- Making large inline helper embedding in generated code a default path

## 5. Out of Scope (Initial Stage)

- Advanced optimization (Lua VM-specific tuning, JIT-prerequisite optimization)
- Full Python syntax / standard library compatibility
- Simultaneous implementation of the PHP backend (order is `Ruby -> Lua -> PHP`)

## 6. Verification Perspectives (Initial)

- `py2lua.py` can generate `.lua` from EAST3.
- No conversion failure on minimum fixtures (`add` / `if_else` / `for_range`).
- Fix regression with `tools/check/check_py2lua_transpile.py` and `tools/unittest/emit/lua/test_py2lua_smoke.py`.

## 7. Container Reference Management Boundary (v1)

- Containers flowing to `object/Any/unknown` boundaries are treated as reference boundaries (ref-boundary).
- `AnnAssign/Assign(Name)` with known type and locally non-escaping allow shallow copy materialization.
  - list/tuple/set/bytes/bytearray: Copy the array region by walking indices
  - dict: Copy key/value pairs by walking with `pairs`
- When undecidable, fall fail-closed to the ref-boundary side.
- Rollback:
  - For problem locations, shift to `Any/object` annotations on the Python input side, or switch to explicit copy (`list(...)` / `dict(...)`).
  - Regression verification uses `python3 tools/check/check_py2lua_transpile.py` and `python3 tools/check/runtime_parity_check.py --case-root sample --targets lua --ignore-unstable-stdout 18_mini_language_interpreter` together.
