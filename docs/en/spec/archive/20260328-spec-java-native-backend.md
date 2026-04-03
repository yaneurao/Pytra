<a href="../../../ja/spec/archive/20260328-spec-java-native-backend.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Java Native Backend Contract Specification

This document defines the contract for the `EAST3 -> Java native emitter` path introduced in `P3-JAVA-NATIVE-01`.
It covers the responsibilities of the input EAST3, fail-closed behavior on unsupported input, the runtime boundary, and differences from the preview output.

## 1. Purpose

- Fix the design boundary when migrating the default path for the Java backend from sidecar bridge to native generation.
- Document "what is supported and how unsupported input fails", even during implementation phases.
- Prevent regressions where `sample/java` reverts to the preview wrapper.

## 2. Differences from the Preview Output

Old path (preview / sidecar, removed):

- `py2java.py` called `transpile_to_js`, generating both `.java` and `.js` simultaneously.
- The Java-side output was a wrapper that executed `node <sidecar.js>` via `ProcessBuilder`, and did not directly express the EAST3 body logic.
- Runtime dependencies were Java runtime + Node.js + JS runtime shim (`pytra/runtime.js`).

After migration (native):

- `py2java.py` defaults to going through the Java native emitter only; no `.js` sidecar is generated.
- The Java-side output directly holds the EAST3 body logic (expressions / statements / control flow / classes) as Java code.
- Runtime dependencies converge to the Java runtime (the repository canonical source is `src/runtime/java/{generated,native}/`), eliminating Node.js dependencies from the default path.

## 3. Input EAST3 Node Responsibilities

The native emitter accepts only EAST3 documents satisfying the following input contract.

- Root is a `dict` with `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is a sequence of EAST3 statement nodes.

Stage responsibilities (minimum set):

- S1 (skeleton): Process the `Module` / `FunctionDef` / `ClassDef` framework.
- S2 (body): Process major statements/expressions (assignment, conditionals, loops, calls, basic types).
- S3 (operational): Process the minimum compatibility including `math` / image runtime calls used in operational samples.

## 4. Fail-Closed Contract

The native path must not silently fall back to sidecar on unsupported input.

- On detecting an unsupported node `kind`, fail immediately with `RuntimeError`.
- The error message must include at least `lang=java`, `node kind`, and `location` (to the extent possible).
- The CLI must exit non-zero and must not output incomplete `.java` files as a success.
- No compatibility mode exists that redirects unsupported input to the sidecar.

## 5. Runtime Boundary

Java artifacts from the native path use only the following as their runtime boundary.

- The Java runtime API under `src/runtime/java/{generated,native}/`.
- JDK standard library (`java.lang`, `java.util`, etc.).

Prohibitions:

- Launching Node.js via `ProcessBuilder`.
- `.js` sidecar generation and dependencies on `pytra/runtime.js`.
- JS bridge-dependent imports inside the Java-generated artifacts.

## 6. Verification Perspectives for Migration

- `tools/check/check_py2java_transpile.py` passes on the native path.
- Fix native-only assumption assertions in `tools/unittest/test_py2java_*.py`.
- `tools/check/runtime_parity_check.py --targets java` monitors output consistency against Python as the baseline.
