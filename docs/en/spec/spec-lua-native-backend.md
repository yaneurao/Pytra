# Lua Native Backend Contract Specification

<a href="../../ja/spec/spec-lua-native-backend.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

This document defines the contract for the `EAST3 -> Lua native emitter` path introduced by `P0-LUA-BACKEND-01`.  
It covers "input EAST3 responsibilities", "fail-closed on unsupported cases", "runtime boundaries", and "out of scope".

## 1. Purpose

- Fix responsibility boundaries when implementing the Lua backend as native direct generation without sidecar dependency.
- Explicitly document supported scope and failure conditions for unsupported cases even in the initial implementation stage.
- Prevent operations that hide inconsistencies via implicit fallback (escaping to another language backend).

## 2. Input EAST3 Node Responsibilities

The Lua native emitter accepts only EAST3 documents that satisfy all of the following.

- Root is `dict` and `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is an EAST3 statement-node list.

Stage responsibilities:

- S1 (skeleton): Minimal path for `Module` / `FunctionDef` / `If` / `ForCore`.
- S2 (body): Assignment, arithmetic, comparison, loops, calls, and minimal built-in set.
- S3 (operation): Incremental support for class/instance/isinstance/import and `math`/image runtime.

## 3. Fail-Closed Contract

If unsupported input is received, fail immediately without escaping to a compatibility path.

- Throw `RuntimeError` as soon as unsupported `kind` / shape is detected.
- Error message must include at least `lang=lua` and failure kind (node/shape).
- CLI exits non-zero and must not treat incomplete `.lua` output as success.
- Do not implicitly fallback to `py2js` / sidecar / EAST2 compatibility.

## 4. Runtime Boundaries

Runtime boundaries for generated Lua code are limited to the following in principle.

- Lua runtime API under `src/runtime/lua/{generated,native}/` (the checked-in repo tree no longer keeps `src/runtime/lua/pytra/**`)
- Lua standard library (`math` / `string` / `table`, etc.)

Prohibited:

- Node.js sidecar bridge dependency
- JS runtime shims as a premise (`pytra/runtime.js`)
- Making large inline helper embedding into generated code the default path

## 5. Out of Scope (Initial Stage)

- Advanced optimization (Lua VM-specific tuning, JIT-assumed optimizations)
- Full compatibility with Python syntax and standard library
- Simultaneous implementation of the PHP backend (order is `Ruby -> Lua -> PHP`)

## 6. Verification Focus (Initial)

- `py2lua.py` can generate `.lua` from EAST3.
- Conversion does not fail on minimal fixtures (`add` / `if_else` / `for_range`).
- Pin regressions with `tools/check_py2lua_transpile.py` and `test/unit/toolchain/emit/lua/test_py2lua_smoke.py`.

## 7. Container Reference Management Boundary (v1)

- Treat containers that flow into the `object/Any/unknown` boundary as a reference boundary (ref-boundary).
- For typed, local non-escape `AnnAssign/Assign(Name)`, allow shallow-copy materialization.
  - list/tuple/set/bytes/bytearray: copy by index-walk over the sequence storage.
  - dict: copy key/value pairs via `pairs` traversal.
- When classification is ambiguous, fail closed to the ref-boundary side.
- Rollback:
  - On problematic cases, move input Python annotations to `Any/object`, or switch to explicit copies (`list(...)` / `dict(...)`).
  - Verify with both `python3 tools/check_py2lua_transpile.py` and `python3 tools/runtime_parity_check.py --case-root sample --targets lua --ignore-unstable-stdout 18_mini_language_interpreter`.
