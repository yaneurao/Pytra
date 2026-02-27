<a href="../../ja/spec/spec-gsk-native-backend.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Go/Swift/Kotlin Native Backend Contract

This document defines the shared contract for the `EAST3 -> Go/Swift/Kotlin native emitter` paths introduced by `P3-GSK-NATIVE-01`.  
Scope: input EAST3 responsibility, fail-closed behavior, runtime boundary, and post-sidecar-removal operational requirements.

## 1. Objective

- Fix ownership boundaries while migrating Go/Swift/Kotlin default output from sidecar bridge to native generation.
- Keep language-specific differences, but unify unsupported-case behavior and runtime boundaries.
- Prevent regressions where `sample/go`, `sample/swift`, or `sample/kotlin` drift back to preview wrappers.

## 2. Difference From Legacy Sidecar Path

Legacy path (preview / sidecar, now removed):

- `py2go.py`, `py2swift.py`, and `py2kotlin.py` emit sidecar JavaScript and language wrappers that invoke Node bridge.
- Generated code often lacks native logic body and becomes a thin `node <sidecar.js>` launcher.
- Runtime dependency is `<lang> runtime + Node.js + JS runtime shim`.

Target (native):

- Default path uses native emitters only and emits no `.js` sidecar.
- Generated code directly contains EAST3 logic (expressions/statements/control flow/classes).
- Sidecar compatibility mode is removed; operation is native-only.

## 3. Input EAST3 Node Responsibility

Native emitters accept only EAST3 documents that satisfy:

- root is a `dict` with `kind == "Module"`;
- `east_stage == 3` (`--east-stage 2` is not accepted);
- `body` is an EAST3 statement-node list.

Shared phased responsibility:

- S1 (skeleton): handle `Module` / `FunctionDef` / `ClassDef` frames.
- S2 (body): handle `Return` / `Expr` / `AnnAssign` / `Assign` / `If` / `ForCore` / `While` and core expressions (`Name`, `Constant`, `Call`, `BinOp`, `Compare`).
- S3 (operational): handle minimal compatibility required by key `sample/py` cases (`math`, image-runtime calls).

## 4. Fail-Closed Contract

Native mode must never silently fallback to sidecar when input is unsupported.

- On unsupported node `kind`, fail immediately (`RuntimeError`-equivalent).
- Error text should include at least `lang`, `node kind`, and location when available.
- CLI must exit non-zero and must not treat partial output as success.
- No escape route to sidecar is allowed for unsupported input.

## 5. Runtime Boundary

Native outputs may rely only on:

- Go: `src/runtime/go/pytra/py_runtime.go` + Go standard library.
- Swift: `src/runtime/swift/pytra/py_runtime.swift` + Swift standard library.
- Kotlin: `src/runtime/kotlin/pytra/py_runtime.kt` + Kotlin/JVM standard library.

Forbidden in default path:

- Node bridge launch via `ProcessBuilder`/`exec`-style flows.
- `.js` sidecar generation and dependency on `sample/<lang>/*.js`.
- JS-bridge-specific imports in generated outputs.

## 6. Migration Verification Focus

- `tools/check_py2go_transpile.py`, `tools/check_py2swift_transpile.py`, and `tools/check_py2kotlin_transpile.py` pass with native-by-default behavior.
- `tools/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --all-samples --ignore-unstable-stdout` keeps parity against Python baseline.
- Regenerated `sample/go`, `sample/swift`, and `sample/kotlin` contain no stale sidecar `.js` outputs.

## 7. Sidecar Retirement Policy (S1-02)

- Remove `--*-backend sidecar` from `py2go.py`, `py2swift.py`, and `py2kotlin.py`; backend switching points are retired.
- Keep generation native-only and emit neither `.js` sidecars nor JS runtime shims.
- Scope default CI regressions, sample regeneration, and parity checks to native paths only.
- Unsupported input on the default path must fail closed; automatic or manual sidecar fallback is not available.
