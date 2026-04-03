<a href="../../../ja/spec/archive/20260328-spec-ruby-native-backend.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Ruby Native Backend Contract Specification

This document defines the contract for the `EAST3 -> Ruby native emitter` path introduced in `P2-RUBY-BACKEND-01`.
It covers the responsibilities of the input EAST3, fail-closed behavior on unsupported input, the runtime boundary, and what is out of scope.

## 1. Purpose

- Fix the boundary for implementing the Ruby backend as a direct native generator that does not rely on sidecar compatibility.
- Document the supported scope and failure conditions on unsupported input, even at the initial implementation stage.
- As with existing backends, prevent the practice of hiding inconsistencies via implicit fallback.

## 2. Input EAST3 Node Responsibilities

The Ruby native emitter accepts only EAST3 documents satisfying the following.

- Root is a `dict` with `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is a sequence of EAST3 statement nodes.

Stage responsibilities:

- S1 (skeleton): Minimum path for `Module` / `FunctionDef` / `ForCore` / `If`.
- S2 (body): Minimum set of assignment, arithmetic, comparison, loops, calls, and built-ins.
- S3 (operational): Incrementally add class/instance/isinstance/import and `math` / image runtime.

## 3. Fail-Closed Contract

On receiving unsupported input, fail immediately without escaping to a compatibility path.

- Raise `RuntimeError` the moment an unsupported `kind` / contract violation is detected.
- The error message must include at least `lang=ruby` and the failure kind (node/shape).
- The CLI must exit non-zero and must not treat incomplete `.rb` output as a success.

## 4. Runtime Boundary

The runtime boundary for Ruby-generated code is limited in principle to the following.

- Minimum helpers within the generated artifacts (`__pytra_*`)
- The Ruby standard library (`Math`, etc.)

Prohibitions:

- Node.js sidecar bridge dependencies
- JS runtime shim prerequisites (`pytra/runtime.js`)
- Compatibility pipelines that fall back to another backend asynchronously

## 5. Out of Scope (Initial Stage)

- Advanced optimization (introducing an optimization layer, Ruby VM-dependent speedups)
- Full compatibility with all Python syntax / standard library
- Simultaneous implementation of PHP/Lua backends (order is `Ruby -> Lua -> PHP`)

## 6. Verification Perspectives (Initial)

- `py2rb.py` can generate `.rb` from EAST3.
- No conversion failure on minimum fixtures (`add` / `if_else` / `for_range`).
- Fix regression for CLI and emitter skeleton in `tools/unittest/emit/rb/test_py2rb_smoke.py`.

## 7. Container Reference Management Boundary (v1)

- Containers flowing to `object/Any/unknown` boundaries are treated as reference boundaries (ref-boundary).
- `AnnAssign/Assign(Name)` with known type and locally non-escaping allow shallow copy materialization.
  - list/tuple/bytes/bytearray: `__pytra_as_list(...).dup`
  - dict: `__pytra_as_dict(...).dup`
- When undecidable, fall fail-closed to the ref-boundary side.
- Rollback:
  - For problem locations, shift to `Any/object` annotations on the Python input side, or switch to explicit copy (`list(...)` / `dict(...)`).
  - Regression verification uses `python3 tools/check/check_py2rb_transpile.py` and `python3 tools/check/runtime_parity_check.py --case-root sample --targets ruby --ignore-unstable-stdout 18_mini_language_interpreter` together.
