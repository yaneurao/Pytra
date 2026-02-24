<a href="../../docs-ja/spec/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Specification Entry Point

`docs/spec/index.md` is the entry page for the full specification set. Details are split into the following files.

- User specification: [User Specification](./spec-user.md)
- Implementation specification: [Implementation Specification](./spec-dev.md)
- Runtime specification: [Runtime Specification](./spec-runtime.md)
- GC specification: [GC Specification](./spec-gc.md)
- Language profile specification: [Language Profile Specification](./spec-language-profile.md)
- Folder responsibility map specification: [Folder Responsibility Map Specification](./spec-folder.md)
- Language-specific specifications: [Language-Specific Specifications](../language/index.md)
- Codex operation specification: [Codex Operation Specification](./spec-codex.md)
- `pylib` module index: [pylib Module Index](./spec-pylib-modules.md)
- Development philosophy: [Development Philosophy](./spec-philosophy.md)

## How To Read

- If you want tool usage, input constraints, and test execution guidance:
  - [User Specification](./spec-user.md)
- If you want implementation policy, module structure, and transpilation rules:
  - [Implementation Specification](./spec-dev.md)
- If you want C++ runtime layout, include mapping rules, and the `Any` mapping policy:
  - [Runtime Specification](./spec-runtime.md)
- If you want RC-based GC policy:
  - [GC Specification](./spec-gc.md)
- If you want `CodeEmitter` JSON profile and hooks specification:
  - [Language Profile Specification](./spec-language-profile.md)
- If you want folder responsibility boundaries (where to place what):
  - [Folder Responsibility Map Specification](./spec-folder.md)
- If you want per-language support details:
  - [Language-Specific Specifications](../language/index.md)
- If you want Codex work rules, TODO operations, and commit operations:
  - [Codex Operation Specification](./spec-codex.md)
- If you want design rationale and the EAST-centric architecture background:
  - [Development Philosophy](./spec-philosophy.md)

## What Codex Checks At Startup

- At startup, Codex reads `docs-ja/spec/index.md` as the canonical entry point, then checks [Codex Operation Specification](./spec-codex.md) and [TODO](../todo/index.md).
