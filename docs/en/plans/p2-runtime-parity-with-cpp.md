# P2: Multi-language Runtime Parity with C++ (Redesign: Strict SoT + Generation-First)

Last updated: 2026-03-05

Related TODO:
- `ID: P2-RUNTIME-PARITY-CPP-02` in `docs/ja/todo/index.md`

Background:
- The previous P2 (`P2-RUNTIME-PARITY-CPP-01`) focused too much on speed of parity and left runtime responsibility boundaries ambiguous.
- This led to repeated policy violations: hand-written language-specific implementations where code should have been generated from pure-Python SoT, custom helper naming, and monolithic embedding.
- Emitter-side direct string-branching on runtime/library function names also persisted and violated IR-side resolution ownership.

Goal:
- Keep API-contract parity with C++ while redefining implementation policy under strict SoT, generation-first, and clear boundary separation.
- Make runtime parity recurrence-resistant through explicit rules, static guards, and parity regressions.

Scope:
- `src/runtime/<lang>/{pytra-core,pytra-gen}/`
- SoT modules in `src/pytra/{std,utils}/`
- Runtime-call paths in `src/toolchain/emit/*/emitter/*.py`
- Audit/generation/parity/CI tooling in `tools/`

Out of scope:
- Large redesign of C++ runtime itself
- Full EAST spec overhaul
- One-shot all-language migration

## Mandatory Rules

These are required, not recommendations:

1. Treat pure-Python implementations in `src/pytra/std/*` and `src/pytra/utils/*` as SoT; do not hand-reimplement equivalent functions per language.
2. Place SoT-derived code under `src/runtime/<lang>/pytra-gen/`; do not mix it into `pytra-core`.
3. Keep passthrough naming for SoT-derived files (e.g. `png.py -> png.<ext>`, `gif.py -> gif.<ext>`); avoid special helper naming.
4. Keep `pytra-core` for language-specific base runtime only; any API representable by SoT belongs to `pytra-gen`.
5. Prohibit emitter-side hardcoded branching for `pytra.std.*` / `pytra.utils.*` names (`callee_name == "..."`, `attr_name == "..."`).
6. Keep runtime/stdlib call resolution in lower/IR; emitters should only render resolved nodes (`runtime_call` family).
7. Do not depend on Python stdlib `ast` inside compiler/backends (selfhost constraint).
8. Require `source:` and `generated-by:` markers for `pytra-gen` outputs, and fail fast in audits.
9. Before parity checks, always clean old artifacts and verify artifact size/CRC32 in addition to stdout.

## Acceptance Criteria

- Old P2 (`P2-RUNTIME-PARITY-CPP-01`) is removed from unfinished TODO and replaced by the new ID.
- Prohibitions and boundaries are documented and enforceable via scripts/CI.
- Naming/placement/marker audits for `pytra-gen` pass for all target languages.
- Hardcoded runtime/library name branching is progressively removed from non-C++ emitters.
- Runtime-difference failures become traceable through parity regressions including artifact size/CRC32.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`

## Breakdown

- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] Remove old P2 (`P2-RUNTIME-PARITY-CPP-01`) from unfinished TODO and replace with new P2.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] Document SoT/pytra-core/pytra-gen boundary and prohibitions in `docs/ja/spec`.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] Create `must-generate / core-allowed` classification table for target `std/utils` modules.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] Add static checks for `pytra-gen` naming-rule violations (passthrough naming).
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] Strengthen marker checks (`source/generated-by`) and placement checks (core/gen mixing), then integrate into CI.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] Audit SoT reimplementation residues in `pytra-core` and feed migration plan to `pytra-gen`.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Use Java as first target to unify runtime API calls into IR-resolved path (remove emitter hardcoding).
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Apply the same policy to other non-C++ backends (`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`).
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] Lint emitter prohibitions (hardcoded library function names) and enforce fail-fast in PR/CI.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] Re-run sample parity across all target languages (including artifact size + CRC32) and lock diffs.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] Reflect local/CI operational procedures in `docs/ja/how-to-use` and `docs/en/how-to-use`.

Decision log:
- 2026-03-05: Replaced legacy P2 with redesigned P2 under strict SoT, generation-first, and boundary separation.
- 2026-03-05: [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] Removed unfinished old-P2 entries from English TODO/plan and replaced them with `P2-RUNTIME-PARITY-CPP-02` decomposition.
