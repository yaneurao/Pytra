<a href="../../ja/spec/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Specification Entry Point

`docs/en/spec/index.md` is the entry page for the full specification set. Details are split into the following files.

- User specification: [User Specification](./spec-user.md)
- Implementation specification: [Implementation Specification](./spec-dev.md)
- Runtime specification: [Runtime Specification](./spec-runtime.md)
- Boxing/Unboxing specification: [Boxing/Unboxing Specification](./spec-boxing.md)
- type_id specification: [type_id Specification](./spec-type_id.md)
- GC specification: [GC Specification](./spec-gc.md)
- Language profile specification: [Language Profile Specification](./spec-language-profile.md)
- Folder responsibility map specification: [Folder Responsibility Map Specification](./spec-folder.md)
- EAST integrated specification (current source of truth): [EAST Specification (Integrated)](./spec-east.md)
- EAST staged responsibilities: [EAST Stage Structure](./spec-east.md#east-stages)
- EAST3 optimizer specification: [EAST3 Optimizer Specification](./spec-east3-optimizer.md)
- C++ backend optimizer specification: [C++ Optimizer Specification](./spec-cpp-optimizer.md)
- C++ list reference semantics: [C++ List Reference Semantics](./spec-cpp-list-reference-semantics.md)
- stdlib signature source-of-truth specification: [stdlib Signature Source-of-Truth](./spec-stdlib-signature-source-of-truth.md)
- Java native backend contract: [Java Native Backend Contract](./spec-java-native-backend.md)
- Lua native backend contract: [Lua Native Backend Contract](./spec-lua-native-backend.md)
- EAST staged file-role mapping (current -> post-migration): [Role Mapping Table](./spec-east.md#east-file-mapping)
- EAST1 build responsibility boundary: [EAST1 Build Boundary](./spec-east.md#east1-build-boundary)
- EAST migration phases: [EAST Migration Phases](./spec-east.md#east-migration-phases)
- Linker specification (EAST link stage): [Linker Specification](./spec-linker.md)
- Language-specific specs: [Language-Specific Specifications](../language/index.md)
- Codex operation spec: [Codex Operation Specification](./spec-codex.md)
- Legacy spec archive: [Spec Archive](./archive/index.md)
- `pylib` module index: [pylib Module Index](./spec-pylib-modules.md)
- Development philosophy: [Development Philosophy](./spec-philosophy.md)

## How To Read

- If you want tool usage, input constraints, and test execution guidance:
  - [User Specification](./spec-user.md)
- If you want implementation policy, module structure, and transpilation rules:
  - [Implementation Specification](./spec-dev.md)
- If you want C++ runtime layout, include mapping rules, and the `Any` mapping policy:
  - [Runtime Specification](./spec-runtime.md)
- If you want the Boxing/Unboxing contract for `Any/object` boundaries:
  - [Boxing/Unboxing Specification](./spec-boxing.md)
- If you want the single-inheritance `type_id` contract (`isinstance` / `issubclass`):
  - [type_id Specification](./spec-type_id.md)
- If you want RC-based GC policy:
  - [GC Specification](./spec-gc.md)
- If you want `CodeEmitter` JSON profile and hooks specification:
  - [Language Profile Specification](./spec-language-profile.md)
- If you want folder responsibility boundaries (where to place what):
  - [Folder Responsibility Map Specification](./spec-folder.md)
- If you want how EAST is operated as three stages (EAST1/EAST2/EAST3):
  - [EAST Stage Structure](./spec-east.md#east-stages)
- If you want the responsibility/contract of the EAST3 optimizer layer (common/language-specific):
  - [EAST3 Optimizer Specification](./spec-east3-optimizer.md)
- If you want post-lowering C++ backend optimization boundaries (`CppOptimizer` vs `CppEmitter`):
  - [C++ Optimizer Specification](./spec-cpp-optimizer.md)
- If you want C++ list alias/share/mutation contracts (value/pyobj migration boundary):
  - [C++ List Reference Semantics](./spec-cpp-list-reference-semantics.md)
- If you want the contract that `pytra/std` is the source of truth for type signatures (removing hardcoded `core.py` branches):
  - [stdlib Signature Source-of-Truth](./spec-stdlib-signature-source-of-truth.md)
- If you want the Java sidecar-removal migration contract (input responsibility / fail-closed / runtime boundary):
  - [Java Native Backend Contract](./spec-java-native-backend.md)
- If you want the Lua native direct-generation contract (input responsibility / fail-closed / runtime boundary):
  - [Lua Native Backend Contract](./spec-lua-native-backend.md)
- If you want the EAST1/EAST2/EAST3 current/post-migration file-role mapping:
  - [Role Mapping Table](./spec-east.md#east-file-mapping)
- If you want the responsibility boundary of the EAST1 build entry (`east1_build.py`):
  - [EAST1 Build Boundary](./spec-east.md#east1-build-boundary)
- If you want the migration order up to EAST3-primary routing:
  - [EAST Migration Phases](./spec-east.md#east-migration-phases)
- If you want the EAST3 link stage (`type_id` assignment, manifest, resume from intermediate files):
  - [Linker Specification](./spec-linker.md)
- If you want per-language feature support status:
  - [Language-Specific Specifications](../language/index.md)
- If you want Codex work rules, TODO operations, and commit operations:
  - [Codex Operation Specification](./spec-codex.md)
- If you want legacy specs (documents not current):
  - [Spec Archive](./archive/index.md)
- If you want design rationale and the EAST-centric architecture background:
  - [Development Philosophy](./spec-philosophy.md)

## What Codex Checks At Startup

- At startup, Codex reads `docs/ja/spec/index.md` as the canonical entry point, then checks [Codex Operation Specification](./spec-codex.md) and [TODO](../todo/index.md).
