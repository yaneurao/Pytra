# Specification Entry Point

<a href="../docs-jp/spec.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


`docs/spec.md` is the entry page for the full specification set. Details are split into the following files.

- User specification: [User Specification](./spec-user.md)
- Implementation specification: [Implementation Specification](./spec-dev.md)
- Runtime specification: [Runtime Specification](./spec-runtime.md)
- GC specification: [GC Specification](./spec-gc.md)
- Language profile specification: [Language Profile Specification](./spec-language-profile.md)
- Language-specific specifications: [Language-Specific Specifications](./language/index.md)
- Codex operation specification: [Codex Operation Specification](./spec-codex.md)
- `pylib` module index: [pylib Module Index](./pylib-modules.md)

## How To Read

- If you want tool usage, input constraints, and test execution guidance:
  - [User Specification](./spec-user.md)
- If you want implementation policy, module structure, and transpilation rules:
  - [Implementation Specification](./spec-dev.md)
- If you want C++ runtime layout and include mapping rules:
  - [Runtime Specification](./spec-runtime.md)
- If you want RC-based GC policy:
  - [GC Specification](./spec-gc.md)
- If you want `CodeEmitter` JSON profile and hooks specification:
  - [Language Profile Specification](./spec-language-profile.md)
- If you want per-language support details:
  - [Language-Specific Specifications](./language/index.md)
- If you want Codex work rules, TODO operations, and commit operations:
  - [Codex Operation Specification](./spec-codex.md)

## What Codex Checks At Startup

- At startup, Codex reads `docs-jp/spec.md` as the canonical entry point, then checks [Codex Operation Specification](./spec-codex.md) and [TODO](../docs-jp/todo.md).

## Current `Any` Policy

- In C++, `Any` is represented as `object` (`rc<PyObj>`).
- `None` is represented as `object{}` (null handle).
- For boxing/unboxing, use `make_object(...)` / `obj_to_*` / `py_to_*`.
