<a href="../../ja/spec/spec-java-native-backend.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Java Native Backend Contract

This document defines the contract for the `EAST3 -> Java native emitter` path introduced by `P3-JAVA-NATIVE-01`.  
Scope: input EAST3 responsibility, fail-closed behavior, runtime boundary, and the diff from preview output.

## 1. Objective

- Fix the design boundary while migrating Java default output from sidecar bridge to native generation.
- Keep implementation phases explicit: what is supported now, and how unsupported cases fail.
- Prevent regressions where `sample/java` drifts back to preview wrappers.

## 2. Difference From Preview Output

Legacy path (preview / sidecar, now removed):

- `py2java.py` calls `transpile_to_js` and emits `.java` + `.js` together.
- Java output is a wrapper that executes `node <sidecar.js>` via `ProcessBuilder`, not a direct Java rendering of EAST3 logic.
- Runtime dependency is Java runtime + Node.js + JS runtime shim (`pytra/runtime.js`).

Target (native):

- Default `py2java.py` path uses only Java native emitter and emits no `.js` sidecar.
- Java output directly contains EAST3 logic (expressions/statements/control flow/classes).
- Runtime dependency converges to Java runtime (`src/runtime/java/pytra/`), removing Node.js from the default path.

## 3. Input EAST3 Node Responsibility

The native emitter accepts only EAST3 documents that satisfy:

- root is a `dict` with `kind == "Module"`;
- `east_stage == 3` (`--east-stage 2` is not accepted);
- `body` is an EAST3 statement-node list.

Phased responsibility:

- S1 (skeleton): handle `Module` / `FunctionDef` / `ClassDef` frames.
- S2 (body): handle core statements/expressions (assignment, conditionals, loops, calls, primitive built-ins).
- S3 (operational): add minimal compatibility needed for practical sample cases (`math`, image runtime calls).

## 4. Fail-Closed Contract

Native mode must never silently fallback to sidecar when input is unsupported.

- On unsupported node `kind`, fail immediately with `RuntimeError`.
- Error text should include at least `lang=java`, `node kind`, and location when available.
- CLI must exit non-zero and must not treat partial `.java` as success.
- No compatibility-mode escape to sidecar is available for unsupported input.

## 5. Runtime Boundary

Generated Java from native mode may rely only on:

- Java runtime APIs under `src/runtime/java/pytra/`;
- JDK standard libraries (`java.lang`, `java.util`, etc.).

Forbidden:

- launching Node.js via `ProcessBuilder`;
- generating `.js` sidecar and depending on `pytra/runtime.js`;
- JS-bridge-specific imports in generated Java.

## 6. Migration Verification Focus

- `tools/check_py2java_transpile.py` passes on the native path.
- `test/unit/test_py2java_*.py` locks native-only behavior.
- `tools/runtime_parity_check.py --targets java` keeps output parity against Python baseline.
