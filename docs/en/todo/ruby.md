<a href="../../ja/todo/ruby.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# TODO — Ruby backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/ruby/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/ruby/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P number first).
- Progress notes and commit messages must include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/en/todo/archive/`.
- **parity test completion criteria: emit + compile + run + stdout match.**
- **Always read the [emitter implementation guidelines](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

- Old toolchain1 Ruby emitter: `src/toolchain/emit/rb/`
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Existing Ruby runtime: `src/runtime/ruby/`
- emitter implementation guidelines: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P0-RUBY-TYPE-ID-CLEANUP: Remove `__pytra_isinstance` from the Ruby runtime

Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Ruby has `is_a?` natively, so `__pytra_isinstance` is not needed.

1. [x] [ID: P0-RUBY-TYPEID-CLN-S1] Remove `__pytra_isinstance` from `src/runtime/ruby/built_in/py_runtime.rb` — removed runtime helper and cleaned up mapping (2026-04-02)
2. [x] [ID: P0-RUBY-TYPEID-CLN-S2] Confirm no regressions in fixture + sample parity — confirmed `138/138 PASS` with `runtime_parity_check_fast.py --targets ruby --east3-opt-level 1` (2026-04-02)

### P1-RUBY-EMITTER: Implement a new Ruby emitter in toolchain2

Context: [docs/ja/plans/p1-ruby-emitter.md](../plans/p1-ruby-emitter.md)

1. [x] [ID: P1-RUBY-EMITTER-S1] Implement a new Ruby emitter in `src/toolchain2/emit/ruby/` — CommonRenderer + override structure. Implementation completed using the TS emitter as reference (2026-03-31)
2. [x] [ID: P1-RUBY-EMITTER-S2] Create `src/runtime/ruby/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` (2026-03-31)
3. [x] [ID: P1-RUBY-EMITTER-S3] Confirm successful Ruby emit for all fixture cases — emit succeeded for all 1031 linked EAST3 cases, 0 failures (2026-03-31)
4. [x] [ID: P1-RUBY-EMITTER-S4] Align the Ruby runtime with toolchain2 emit output — added 15 missing functions to py_runtime.rb (2026-03-31)
5. [x] [ID: P1-RUBY-EMITTER-S5] Pass fixture + sample Ruby run parity (`ruby`) — fixture parity `138/138 PASS`; resolved 5 remaining cases (`gc_reassign`, `integer_promotion`, `obj_attr_space`, `str_repr_containers`, `super_init`) (2026-04-02)
6. [x] [ID: P1-RUBY-EMITTER-S6] Pass Ruby parity for stdlib (`--case-root stdlib`) — confirmed stdlib `16/16 PASS`, sample `18/18 PASS`, fixture `138/138 PASS`. The remaining `12_sort_visualizer` case was resolved by fixing `Swap` implementation in the Ruby emitter (2026-04-02)

### P2-RUBY-LINT-FIX: Fix hardcode violations in the Ruby emitter

1. [x] [ID: P2-RUBY-LINT-S1] Confirm `check_emitter_hardcode_lint.py` reports 0 Ruby violations — resolved class name / Python syntax / skip pure Python violations and confirmed 0 (2026-04-02)

### P20-RUBY-SELFHOST: Transpile toolchain2 to Ruby using the Ruby emitter and confirm it runs

1. [ ] [ID: P20-RUBY-SELFHOST-S0] Add type annotations to selfhost target code (shared with other languages)
2. [ ] [ID: P20-RUBY-SELFHOST-S1] Emit all toolchain2 .py files to Ruby and confirm they run
3. [ ] [ID: P20-RUBY-SELFHOST-S2] Place selfhost Ruby golden files
4. [ ] [ID: P20-RUBY-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root fixture` passes fixture parity
5. [ ] [ID: P20-RUBY-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ruby --emit-target ruby --case-root sample` passes sample parity
