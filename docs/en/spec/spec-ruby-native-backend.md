<a href="../../ja/spec/spec-ruby-native-backend.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Ruby Native Backend Contract

This document defines the contract for the `EAST3 -> Ruby native emitter` path introduced in `P2-RUBY-BACKEND-01`.  
Scope: input EAST3 responsibility, fail-closed behavior, runtime boundary, and out-of-scope items.

## 1. Objective

- Fix the design boundary for Ruby backend as native direct generation (no sidecar compatibility fallback).
- Keep support scope and failure behavior explicit even in the early implementation phase.
- Prevent hidden inconsistencies caused by implicit fallback paths.

## 2. Input EAST3 Node Responsibility

The Ruby native emitter accepts only EAST3 documents that satisfy:

- root is a `dict` with `kind == "Module"`;
- `east_stage == 3` (`--east-stage 2` is not accepted);
- `body` is an EAST3 statement-node list.

Phased responsibility:

- S1 (skeleton): minimal path for `Module` / `FunctionDef` / `ForCore` / `If`.
- S2 (body): assignments, arithmetic, comparisons, loops, calls, and minimum built-ins.
- S3 (operational): staged support for class/instance/isinstance/import plus `math` and image runtime calls.

## 3. Fail-Closed Contract

Unsupported input must fail immediately without escaping to compatibility paths.

- Raise `RuntimeError` as soon as unsupported `kind` or contract violation is detected.
- Error text should include at least `lang=ruby` and the failure kind (node/shape).
- CLI must exit non-zero and must not treat partial `.rb` output as success.

## 4. Runtime Boundary

Runtime boundary for generated Ruby code is limited to:

- minimal helpers embedded in generated source (`__pytra_*`),
- Ruby standard library (`Math`, etc.).

Forbidden:

- Node.js sidecar bridge dependency,
- JS runtime shim assumptions (`pytra/runtime.js`),
- async fallback to other toolchain.emit.

## 5. Out of Scope (Initial Phase)

- advanced optimizations (optimizer layer, Ruby-VM-specific tuning),
- full Python grammar/stdlib compatibility,
- parallel implementation of PHP/Lua backends (order is `Ruby -> Lua -> PHP`).

## 6. Initial Verification Focus

- `py2rb.py` generates `.rb` from EAST3 input.
- minimal fixtures (`add` / `if_else` / `for_range`) transpile without failure.
- `test/unit/toolchain/emit/rb/test_py2rb_smoke.py` locks CLI/emitter skeleton behavior.

## 7. Container Reference Management Boundary (v1)

- Treat containers that flow into the `object/Any/unknown` boundary as a reference boundary (ref-boundary).
- For typed, local non-escape `AnnAssign/Assign(Name)`, allow shallow-copy materialization.
  - list/tuple/bytes/bytearray: `__pytra_as_list(...).dup`
  - dict: `__pytra_as_dict(...).dup`
- When classification is ambiguous, fail closed to the ref-boundary side.
- Rollback:
  - On problematic cases, move input Python annotations to `Any/object`, or switch to explicit copies (`list(...)` / `dict(...)`).
  - Verify with both `python3 tools/check_py2rb_transpile.py` and `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --ignore-unstable-stdout 18_mini_language_interpreter`.
