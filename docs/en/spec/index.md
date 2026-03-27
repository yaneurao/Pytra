<a href="../../ja/spec/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Specification Entry Point

`docs/ja/spec/index.md` is the entry page to the full specification set. The detailed content is split into the following files.

- User specification: [User Specification](./spec-user.md)
- Python compatibility guide: [Python Compatibility Guide](./spec-python-compat.md)
- Implementation specification: [Implementation Specification](./spec-dev.md)
- Runtime specification: [Runtime Specification](./spec-runtime.md)
- Boxing and unboxing specification: [Boxing and Unboxing Specification](./spec-boxing.md)
- `type_id` specification: [type_id Specification](./spec-type_id.md)
- Tagged-union specification: [Tagged Union Specification](./spec-tagged-union.md)
- GC specification: [GC Specification](./spec-gc.md)
- Language-profile specification: [Language Profile Specification](./spec-language-profile.md)
- Folder responsibility map specification: [Folder Responsibility Map Specification](./spec-folder.md)
- EAST integrated specification, current source of truth: [EAST Specification](./spec-east.md)
- EAST1 specification, parse output contract: [EAST1 Specification](./spec-east1.md)
- EAST2 specification, resolve output contract: [EAST2 Specification](./spec-east2.md)
- Responsibilities of the three EAST stages: [EAST Stages](./spec-east.md#east-stages)
- EAST3 optimizer-layer specification: [EAST3 Optimizer Specification](./spec-east3-optimizer.md)
- C++ backend optimizer-layer specification: [C++ Optimizer Specification](./spec-cpp-optimizer.md)
- C++ list reference-semantics specification: [C++ List Reference Semantics](./spec-cpp-list-reference-semantics.md)
- stdlib signature source-of-truth specification: [stdlib Signature Source-of-Truth](./spec-stdlib-signature-source-of-truth.md)
- Java native backend contract specification: [Java Native Backend Contract](./spec-java-native-backend.md)
- Lua native backend contract specification: [Lua Native Backend Contract](./spec-lua-native-backend.md)
- Zig native backend contract specification: [Zig Native Backend Contract](./spec-zig-native-backend.md)
- Shared contract for backend emitters: [Emitter Implementation Guidelines](./spec-emitter-guide.md)
- Runtime `mapping.json` specification: [runtime mapping Specification](./spec-runtime-mapping.md)
- File-responsibility mapping for current and post-migration EAST stages: [Role Mapping Table](./spec-east.md#east-file-mapping)
- Responsibility boundary for the EAST1 build layer: [EAST1 Build Boundary](./spec-east.md#east1-build-boundary)
- EAST migration phases: [EAST Migration Phases](./spec-east.md#east-migration-phases)
- Linker specification, EAST linking: [Linker Specification](./spec-linker.md)
- Compile and link pipeline plan: [Compile / Link Pipeline](../plans/p2-compile-link-pipeline.md)
- Language-specific specifications: [Language-Specific Specifications](../language/index.md)
- Operational specification for Codex: [Codex Operation Specification](./spec-codex.md)
- Legacy specification archive: [Specification Archive](./archive/index.md)
- `pylib` module list: [pylib Module Index](./spec-pylib-modules.md)
- Development philosophy: [Development Philosophy](./spec-philosophy.md)

## How to read it

- If you want tool usage, input constraints, or how to run tests:
  [User Specification](./spec-user.md)
- If you want differences from Python or unsupported features:
  [Python Compatibility Guide](./spec-python-compat.md)
- If you want to check `import` rules, the unified `pytra.*` rules, usable types, or the module list:
  [User Specification, Python Input Specification](./spec-user.md#2-python-input-specification)
- If you want implementation policy, module layout, or transpilation rules:
  [Implementation Specification](./spec-dev.md)
- If you want C++ runtime placement, include-handling rules, or how `Any` is represented in C++:
  [Runtime Specification](./spec-runtime.md)
- If you want the boxing and unboxing contract at the `Any/object` boundary:
  [Boxing and Unboxing Specification](./spec-boxing.md)
- If you want the single-inheritance `type_id` contract for `isinstance` and `issubclass`:
  [type_id Specification](./spec-type_id.md)
- If you want tagged-union declarations for `type X = A | B | ...`, plus `isinstance` and cast narrowing:
  [Tagged Union Specification](./spec-tagged-union.md)
- If you want the RC-based GC policy:
  [GC Specification](./spec-gc.md)
- If you want the `CodeEmitter` JSON profile and hook contract:
  [Language Profile Specification](./spec-language-profile.md)
- If you want to know what belongs in which folder and why:
  [Folder Responsibility Map Specification](./spec-folder.md)
- If you want to understand how EAST is operated as three stages, EAST1, EAST2, and EAST3:
  [EAST Stages](./spec-east.md#east-stages)
- If you want the responsibilities and contracts of the EAST3 optimizer layer, shared and language-specific:
  [EAST3 Optimizer Specification](./spec-east3-optimizer.md)
- If you want the responsibility split for later C++ backend optimization, `CppOptimizer` versus `CppEmitter`:
  [C++ Optimizer Specification](./spec-cpp-optimizer.md)
- If you want the C++ list aliasing, sharing, and destructive-update contract, including the value/pyobj migration boundary:
  [C++ List Reference Semantics](./spec-cpp-list-reference-semantics.md)
- If you want the contract that `pytra/std` is the source of truth for type signatures, replacing hard-coded logic in `core.py`:
  [stdlib Signature Source-of-Truth](./spec-stdlib-signature-source-of-truth.md)
- If you want the Java backend migration contract for removing sidecars, input responsibility, fail-closed, and runtime boundary:
  [Java Native Backend Contract](./spec-java-native-backend.md)
- If you want the Lua backend contract for direct native generation, input responsibility, fail-closed, and runtime boundary:
  [Lua Native Backend Contract](./spec-lua-native-backend.md)
- If you want the Zig backend contract, unsupported `try/except`, unsupported inheritance, and reference-semantics constraints:
  [Zig Native Backend Contract](./spec-zig-native-backend.md)
- If you want new-backend development rules, container reference-semantics requirements, or the `yields_dynamic` contract:
  [Emitter Implementation Guidelines](./spec-emitter-guide.md)
- If you want the file-responsibility mapping for current and post-migration EAST1, EAST2, and EAST3:
  [Role Mapping Table](./spec-east.md#east-file-mapping)
- If you want the responsibility boundary of the EAST1 build entrypoint, `east1_build.py`:
  [EAST1 Build Boundary](./spec-east.md#east1-build-boundary)
- If you want the migration order until EAST3 becomes the main path:
  [EAST Migration Phases](./spec-east.md#east-migration-phases)
- If you want the EAST3 linking stage, `type_id` resolution, manifest handling, or intermediate-file resume:
  [Linker Specification](./spec-linker.md)
- If you want feature support by language:
  [Language-Specific Specifications](../language/index.md)
- If you want Codex work rules, TODO handling, or commit rules:
  [Codex Operation Specification](./spec-codex.md)
- If you want older, no longer current specifications:
  [Specification Archive](./archive/index.md)
- If you want the design philosophy and background of the EAST-centered architecture:
  [Development Philosophy](./spec-philosophy.md)

## What Codex checks at startup

- At startup, Codex reads `docs/ja/spec/index.md` as the entry point, then checks the [Codex Operation Specification](./spec-codex.md) and [TODO](../todo/index.md).
