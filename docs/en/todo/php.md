<a href="../../ja/todo/php.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — PHP backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/php/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/php/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 PHP emitter: `src/toolchain/emit/php/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing PHP runtime: `src/runtime/php/`
- emitter implementation guidelines: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P20-PHP-SELFHOST: Transpile toolchain2 to PHP using the PHP emitter and confirm it runs

1. [ ] [ID: P20-PHP-SELFHOST-S0] Add type annotations to selfhost target code (shared with other languages)
2. [ ] [ID: P20-PHP-SELFHOST-S1] Emit all toolchain2 .py files to PHP and confirm they run
3. [ ] [ID: P20-PHP-SELFHOST-S2] Place selfhost PHP golden files
4. [ ] [ID: P20-PHP-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root fixture` passes fixture parity
5. [ ] [ID: P20-PHP-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root sample` passes sample parity
