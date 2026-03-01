# P3: Isolate C# Selfhost-Originated Fixes from CodeEmitter

Last updated: 2026-03-01

Related TODO:
- `ID: P3-CODEEMITTER-CS-ISOLATION-01` in `docs/ja/todo/index.md`

Background:
- During C# selfhost support, adjustments originating from C#-specific constraints were mixed into `CodeEmitter` (common base).
- User policy prioritizes: "Do not modify common compiler layers for unsupported C# transpiler issues."
- If language-specific workarounds remain in common layers, regression surface and maintenance cost rise for other backends.

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
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] Move "C#-specific" changes into `CSharpEmitter` / C# runtime / selfhost-preparation layers.
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] Remove C#-specific workaround code from `CodeEmitter` and restore common implementation.
- [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] Run unit/selfhost regressions and confirm C# pass maintenance and no regression in other backends.

Decision Log:
- 2026-03-01: Per user instruction, explicitly set policy to avoid bringing C#-specific constraints into `CodeEmitter`, and decided to create a P3 plan before implementation.
