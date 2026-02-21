# Specification Entry Point

`docs-en/spec.md` is the entry page for the full specification set. Details are split into the following files.

- User specification: [`docs-en/spec-user.md`](./spec-user.md)
- Implementation specification: [`docs-en/spec-dev.md`](./spec-dev.md)
- Runtime specification: [`docs-en/spec-runtime.md`](./spec-runtime.md)
- Language profile specification: [`docs-en/spec-language-profile.md`](./spec-language-profile.md)
- Codex operation specification: [`docs-en/spec-codex.md`](./spec-codex.md)
- `pylib` module index: [`docs-en/pylib-modules.md`](./pylib-modules.md)

## How To Read

- If you want tool usage, input constraints, and test execution guidance:
  - [`docs-en/spec-user.md`](./spec-user.md)
- If you want implementation policy, module structure, and transpilation rules:
  - [`docs-en/spec-dev.md`](./spec-dev.md)
- If you want C++ runtime layout and include mapping rules:
  - [`docs-en/spec-runtime.md`](./spec-runtime.md)
- If you want `CodeEmitter` JSON profile and hooks specification:
  - [`docs-en/spec-language-profile.md`](./spec-language-profile.md)
- If you want Codex work rules, TODO operations, and commit operations:
  - [`docs-en/spec-codex.md`](./spec-codex.md)

## What Codex Checks At Startup

- At startup, Codex reads `docs-en/spec.md` as the entry point, then checks [`docs-en/spec-codex.md`](./spec-codex.md) and [`docs-en/todo.md`](./todo.md).

## Current `Any` Policy

- In C++, `Any` is represented as `object` (`rc<PyObj>`).
- `None` is represented as `object{}` (null handle).
- For boxing/unboxing, use `make_object(...)` / `obj_to_*` / `py_to_*`.

