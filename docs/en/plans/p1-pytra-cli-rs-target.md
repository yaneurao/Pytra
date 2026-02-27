# P1: Add Rust target to unified CLI `./pytra`

Last updated: 2026-02-27

Related TODO:
- `ID: P1-PYTRA-CLI-RS-01` in `docs/ja/todo/index.md`

Background:
- Current `./pytra` supports only `--target cpp`, so Rust transpilation still requires calling `py2rs.py` directly.
- If we standardize entrypoints around `./pytra`, excluding Rust breaks operational consistency.
- For temporary outputs, we should avoid creating new top-level folders and consolidate into existing `out/` (or `/tmp` when necessary).

Goal:
- Make Rust transpilation executable from `./pytra`, using the same entrypoint model as C++.

In scope:
- Extend target dispatch in `src/pytra/cli.py` (`rs`)
- Output-path behavior for `--target rs` (`--output` / `--output-dir`)
- Add Rust examples to unified CLI section in `docs/ja/how-to-use.md`

Out of scope:
- Semantic changes to the Rust backend itself (`py2rs.py`)
- Advanced Rust `--build` integration (such as Cargo wiring)
- Deprecating/removing the existing `py2rs.py` CLI

Acceptance criteria:
- `./pytra INPUT.py --target rs --output OUT.rs` succeeds.
- `./pytra INPUT.py --target rs --output-dir DIR` generates `.rs` files under `DIR`.
- `./pytra --help` displays `rs`.
- `docs/ja/how-to-use.md` includes a `./pytra --target rs` usage example.
- Temporary-output policy (avoid new top-level folder sprawl) is documented.

Validation commands:
- `./pytra --help`
- `./pytra test/fixtures/core/add.py --target rs --output /tmp/add.rs`
- `./pytra test/fixtures/core/add.py --target rs --output-dir out/rs_demo`
- `python3 -m py_compile src/pytra/cli.py`

Decision log:
- 2026-02-27: By user request, fixed policy to register `--target rs` as a `P1` TODO item.

## Breakdown

- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-01] Add `--target rs` dispatch in `src/pytra/cli.py` and integrate `py2rs.py` invocation.
- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-02] Define Rust output behavior for `--output` / `--output-dir`, including collision handling (extension and same-name output).
- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-03] Add Rust examples to unified CLI section in `docs/ja/how-to-use.md`, and document output policy (`out/` / `/tmp`).
