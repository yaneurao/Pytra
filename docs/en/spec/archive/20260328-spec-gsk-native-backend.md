<a href="../../../ja/spec/archive/20260328-spec-gsk-native-backend.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Go/Swift/Kotlin Native Backend Contract Specification

This document defines the shared contract for the `EAST3 -> Go/Swift/Kotlin native emitter` path introduced in `P3-GSK-NATIVE-01`.
It covers the responsibilities of the input EAST3, fail-closed behavior on unsupported input, the runtime boundary, and operational requirements after sidecar removal.

## 1. Purpose

- Fix the responsibility boundary when migrating the default path for Go / Swift / Kotlin backends from sidecar bridge to native generation.
- Unify failure behavior on unsupported input and the runtime boundary, while tolerating per-language differences.
- Prevent regressions where `sample/go` / `sample/swift` / `sample/kotlin` revert to preview wrappers.

## 2. Differences from the Old Sidecar Path

Old path (preview / sidecar, removed):

- `py2go.py` / `py2swift.py` / `py2kotlin.py` generated sidecar JavaScript, and each language side output a Node bridge wrapper.
- The generated code did not contain the actual logic body; it tended to be a thin wrapper executing `node <sidecar.js>`.
- Runtime dependencies were `<lang> runtime + Node.js + JS runtime shim`.

After migration (native):

- The default path goes through the native emitter only; no `.js` sidecar is generated.
- The generated code directly holds the EAST3 body logic (expressions / statements / control flow / classes) as code in the target language.
- Sidecar compatibility mode is abolished; operation uses the native path exclusively.

## 3. Input EAST3 Node Responsibilities

The native emitter accepts only EAST3 documents satisfying the following input contract.

- Root is a `dict` with `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is a sequence of EAST3 statement nodes.

Common stage responsibilities:

- S1 (skeleton): Process the `Module` / `FunctionDef` / `ClassDef` framework.
- S2 (body): Process `Return` / `Expr` / `AnnAssign` / `Assign` / `If` / `ForCore` / `While` and major expressions (`Name` / `Constant` / `Call` / `BinOp` / `Compare`).
- S3 (operational): Process the minimum compatibility required for `math` / image runtime calls needed by major `sample/py` cases.

## 4. Fail-Closed Contract

The native path must not silently fall back to sidecar on unsupported input.

- On detecting an unsupported node `kind`, fail immediately (equivalent to `RuntimeError`).
- The error message must include at least `lang`, `node kind`, and `location` (to the extent possible).
- The CLI must exit non-zero and must not output incomplete generated artifacts as a success.
- There is no escape path that redirects unsupported input to the sidecar.

## 5. Runtime Boundary

Native-generated artifacts use only the following runtime boundaries.

- Go: `src/runtime/go/{generated,native}/` + Go standard library.
- Swift: `src/runtime/swift/{generated,native}/` + Swift standard library.
- Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM standard library.

Prohibitions (default path):

- Bridge implementations that launch Node.js via `ProcessBuilder` / `exec`, etc.
- `.js` sidecar generation and `sample/<lang>/*.js` dependencies.
- JS bridge-dependent imports inside the generated artifacts.

## 6. Verification Perspectives for Migration

- `tools/check/check_py2go_transpile.py` / `tools/check/check_py2swift_transpile.py` / `tools/check/check_py2kotlin_transpile.py` pass with native as the default.
- `tools/check/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --ignore-unstable-stdout` monitors output consistency against Python as the baseline.
- Confirm that no sidecar `.js` files remain when regenerating `sample/go` / `sample/swift` / `sample/kotlin`.

## 7. Sidecar Removal Policy (S1-02)

- Remove `--*-backend sidecar` from `py2go.py` / `py2swift.py` / `py2kotlin.py`, and remove the backend switching point.
- The generation path is native only; no `.js` sidecar or JS runtime shims are generated at all.
- CI's default regression, sample regeneration, and parity verification monitor only the native path.
- When unsupported input is detected in the default path, stop fail-closed (no automatic or manual fallback to sidecar is permitted).

## 8. Container Reference Management Boundary (v1)

- Common vocabulary:
  - `container_ref_boundary`: Paths flowing into `Any/object/unknown/union(including any)`.
  - `typed_non_escape_value_path`: Paths with known type and locally non-escaping.
- Operational rules:
  - `container_ref_boundary`: Treat as a reference; avoid unnecessary implicit copies.
  - `typed_non_escape_value_path`: Allow shallow-copy materialization (prioritize alias separation).
  - When undecidable, fall fail-closed to `container_ref_boundary`.
- Rollback:
  - For locations where generated differences cause problems, force ref-boundary by adjusting the input-side type annotations toward `Any/object`.
  - Verification uses `check_py2{go,swift,kotlin}_transpile.py` and `runtime_parity_check.py` together.
