<a href="../../ja/plans/p3-codeemitter-cs-isolation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P3: Isolate C# Selfhost-Originated Fixes from CodeEmitter

Last updated: 2026-03-01

Related TODO:
- `ID: P3-CODEEMITTER-CS-ISOLATION-01` in `docs/ja/todo/index.md`

Background:
- During C# selfhost support, adjustments originating from C#-specific constraints were mixed into `CodeEmitter` (common base).
- User policy prioritizes: "Do not modify common compiler layers for unsupported C# transpiler issues."
- If language-specific workarounds remain in common layers, regression surface and maintenance cost rise for other toolchain.emit.

Objective:
- Re-limit `CodeEmitter` responsibility to "logic common to all backends" and move C#-specific workarounds to `CSharpEmitter` / C# runtime / selfhost-preparation layers.

Scope:
- `src/pytra/compiler/east_parts/code_emitter.py`
- `src/hooks/cs/emitter/cs_emitter.py`
- `tools/prepare_selfhost_source_cs.py` / `src/runtime/cs/*` if needed
- Regression checks: `test/unit/test_code_emitter.py` / `test/unit/test_py2cs_smoke.py` / `tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py`

Out of scope:
- New C# backend features (optimization or syntax expansion)
- Selfhost modifications on JS/TS/Go/Java/Swift/Kotlin sides
- New specs in EAST3 optimization layer

Acceptance Criteria:
- Changes in `CodeEmitter` that were made for C#-specific reasons are classified with rationale as either "migrated" or "common-required."
- C#-specific implementations are moved into C# side (`CSharpEmitter`, etc.), and `CodeEmitter` returns to backend-neutral form.
- `test_code_emitter` / `test_py2cs_smoke` pass.
- `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` keep C# status as `pass`.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_code_emitter.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`

Breakdown:
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] Inventory `CodeEmitter` diffs since `v0.4.0` and classify into "common-required / C#-specific / pending judgment".
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] Document judgment criteria for "common-required" (backend neutrality, cross-language usage evidence, fail-closed necessity).
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] Move "C#-specific" changes into `CSharpEmitter` / C# runtime / selfhost-preparation layers.
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] Remove C#-specific workaround code from `CodeEmitter` and restore common implementation.
- [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] Run unit/selfhost regressions and confirm C# pass maintenance and no regression in other toolchain.emit.

## S1-01 Audit (`v0.4.0=96898f02` and later)

This classification is based on `git log 96898f02..HEAD -- src/pytra/compiler/east_parts/code_emitter.py`.

### Common-required (keep candidates)

1. `fe81e0a1` (dependency-collection API)
   - `require_dep*` / `finalize_deps` are used by the Go emitter and are not C#-specific.
2. `72e3895a` (`import_resolution` acceptance)
   - Multiple backends share `load_import_bindings_from_meta`; needed for IR-contract backward compatibility.
3. `11d50618` (ForCore downrange mode resolution)
   - `cs/js/ts/rs/lua` use `resolve_forcore_static_range_mode`.
4. `cc49329e` (`rc_new` type-restoration helper)
   - Originates from C++ output-quality improvement, not C# selfhost-only reasons.

### C#-specific (migration candidates)

1. `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` group (`6ff2dbe7` to `f9e3a5b6`)
   - Relaxations like `any_dict_get*` / `emit_with_scope` / `Any` conversion of hook return handling were introduced for C# selfhost object-type consistency.
2. `5d00eda8` / `a101d8d5` / `003424db`
   - Adjustments mainly aimed at passing C# selfhost stage1/multistage.

### Pending judgment

1. ASCII-check helper group (`_is_ascii_*`)
   - Implementation intent started from C# selfhost, but may also improve common stability for identifier/hook-name normalization.
2. Key-normalizing copy in `any_to_dict_or_empty`
   - Originated from C# object-safe handling, but may be valuable as common fail-closed hardening against non-string key mixing.

## S1-02 Judgment Criteria (Common-Required)

We lock "common-required" classification on these three axes:

1. Backend neutrality
   - API/behavior does not assume language-specific type constraints (e.g., C# `object` constraints).
2. Cross-language usage evidence
   - Actually called by non-C# emitters, or required by IR contract.
3. Fail-closed necessity
   - Removing it would reduce safety (e.g., unresolved imports, broken range-mode decisions).

Changes that satisfy none of the three are classified, by default, as migration candidates to the C# side.

Decision Log:
- 2026-03-01: Per user instruction, explicitly set policy to avoid bringing C#-specific constraints into `CodeEmitter`, and decided to create a P3 plan before implementation.
- 2026-03-02: As S1-01, audited `CodeEmitter` diffs since `v0.4.0` by commit and created a 3-way classification: common-required / C#-specific / pending judgment.
- 2026-03-02: As S1-02, documented criteria for common-required classification (backend neutrality, cross-language usage evidence, fail-closed necessity).
- 2026-03-02: As S2-01, moved scope-name normalization (`_normalize_scope_names`) from `CodeEmitter` to `CSharpEmitter`, restoring the common layer to a `set[str]` assumption. `test_code_emitter` / `test_py2cs_smoke` passed, and two `check_py2cs_transpile` failures (`yield_generator_min.py` / `tuple_assign.py`) remain known pre-existing issues.
- 2026-03-02: As S2-02, restored reverse traversal in `is_declared` from the C#-specific `while` workaround back to the common `range(...,-1,-1)` implementation, and restored `_const_int_literal` return annotation to `int|None`. unit/smoke passed, and two `check_py2cs_transpile` failures remain known pre-existing issues.
- 2026-03-02: As S3-01, re-ran `test_code_emitter` / `test_py2cs_smoke` / `check_multilang_selfhost_stage1 --strict-stage1` / `check_multilang_selfhost_multistage`. C# recovered to `pass` on stage1/native and multistage (stage1/2/3). Also organized the `transpile_cli` helper extraction list (`prepare_selfhost_source.py`) and C# selfhost compile blockers (typed containers / keyword args / dict key types).
