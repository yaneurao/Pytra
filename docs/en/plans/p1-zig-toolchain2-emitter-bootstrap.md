<a href="../../en/plans/p1-zig-toolchain2-emitter-bootstrap.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1 Zig toolchain2 emitter bootstrap

Last updated: 2026-04-02

Target IDs:
- P1-ZIG-EMITTER-S1
- P1-ZIG-EMITTER-S2

Purpose:
- Add a Zig emit path under `src/toolchain2/emit/zig/` so that Zig can be selected from the toolchain2 pipeline.
- Add `src/runtime/zig/mapping.json` and `src/toolchain2/emit/profiles/zig.json` to establish the prerequisites for lower/emit/parity.

Background:
- Zig has a native emitter on the old toolchain1 side, but on the toolchain2 side the emit profile, mapping, and CLI path are not yet in place.
- Because the parity check's source of truth is the toolchain2 pipeline, a bootstrap that lets toolchain2 run Zig is needed first.

Scope of this task:
- Add `toolchain2/emit/zig/`
- Add the Zig path to `pytra-cli2` / `runtime_parity_check_fast.py` / target profile
- Add `src/runtime/zig/mapping.json`
- Add `src/toolchain2/emit/profiles/zig.json`

Out of scope:
- Full rewrite of the Zig emitter
- Complete parity for all fixtures
- Full resolution of hardcode lint violations
- Additional fixes to the runtime API

Acceptance Criteria:
1. toolchain2 accepts `--target zig` in lower/emit.
2. The required files for the Zig runtime mapping/profile exist and pass `check_mapping_json.py`.
3. At least one case succeeds end-to-end with `emit + zig build-exe + run`.

Decision Log:
- 2026-04-02: First priority is the bootstrap — establish the Zig emit path, profile, mapping, and parity execution pipeline on the toolchain2 side. Full CommonRenderer migration continues in a follow-up task.
