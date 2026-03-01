<a href="../../ja/spec/spec-codex.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Codex Operation Specification (Pytra)

This document defines the operational rules Codex follows while working.

## 1. Startup Checks

- At Codex startup, first check `docs/ja/spec/index.md` and `docs/ja/todo/index.md`.
- From unfinished (`[ ]`) items in `docs/ja/todo/index.md`, include tasks aligned with the current request.

## 1.1 Documentation Language Rules

- Treat `docs/ja/` as the source of truth and update Japanese docs first.
- In normal operation, do not edit `docs/en/` (English docs) first; update `docs/ja/` first.
- User instructions are primarily Japanese, and Codex assumes Japanese working instructions by default.
- `docs/en/` may be updated later as delayed translation when needed, and temporary sync lag is allowed.
- If Japanese and English docs diverge, judge based on `docs/ja/`.
- New top-level files directly under `docs/ja/` are prohibited by default; explicit instruction in the same turn is required if needed.
- As an exception, `docs/ja/AGENTS.md` is allowed as a permanent bootstrap entry.
- Root `AGENTS.md` is a local-only pointer (`.gitignore` target) and is not tracked in Git.
- As exceptions, Codex may autonomously create new files under `docs/ja/plans/`, `docs/ja/language/`, `docs/ja/todo/archive/`, `docs/ja/spec/`, and `docs/ja/news/` within the operation rules.

## 2. TODO Execution Rules

- Treat `docs/ja/todo/index.md` as a continuous backlog.
- Keep only unfinished tasks in `docs/ja/todo/index.md`; when an entire section is complete (all items `[x]`), move it to `docs/ja/todo/archive/index.md` (index) and `docs/ja/todo/archive/YYYYMMDD.md` (body).
- For priority override, do not use `docs/ja/todo2.md`; provide `target IDs` / `done criteria` / `out of scope` in chat instructions (template: `docs/ja/plans/instruction-template.md`).
- Execute unfinished items in priority order (smallest `P<number>` first; first item from top within the same priority).
- If even one `P0` item is unfinished, do not start `P1` or lower without explicit override instruction.
- Keep progress memos in `docs/ja/todo/index.md` to one-line summaries; write detailed decision and verification logs into `Decision log` in context files (`docs/ja/plans/*.md`).
- Large tasks may be split into child tasks (`-S1`, `-S2`) in context files; `tools/check_todo_priority.py` permits the top unfinished `ID` and its child IDs.
- In any turn adding progress logs to `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, pass `python3 tools/check_todo_priority.py` (`plans` side counts only date lines in `Decision log` for progress checks).
- If uncommitted diffs remain due to interruption, finish the same `ID` or revert diffs before moving to another `ID`.
- Update check status when a task is completed.

## 3. Documentation Sync Rules

- Update `README.md` as needed when specs/features/procedures change.
- Check consistency for docs linked from `README.md` (`docs/ja/how-to-use.md`, `sample/readme-ja.md`, `docs/ja/spec/index.md`, `docs/ja/plans/pytra-wip.md`, `docs/ja/spec/spec-philosophy.md`) and update together when needed.
- Include "no implementation-doc mismatch left" in completion criteria.
- If scripts in `tools/` are added/removed/renamed, update `docs/ja/spec/spec-tools.md` at the same time.
- Keep only the latest 3 items in "Latest News" in `docs/ja/README.md`; append older items to major-version files (for example, `docs/ja/news/v0-releases.md`) and update `docs/ja/news/index.md`.
- Terminology rule: when referring to type annotation, write "type annotation" explicitly.
- Writing rule: when describing features/folder structure, always state the purpose.
- Writing rule: state not only where to place but also why to place there, to avoid responsibility mixing between `std` and `tra`.
- Keep only current specs under `docs/ja/spec/`; move retired specs to `docs/ja/spec/archive/YYYYMMDD-<slug>.md`.
- Maintain `docs/ja/spec/archive/index.md` as the retired-spec index and append links whenever archive files are added.

## 4. Commit Operations

- When work is logically coherent, commits may be made without per-commit user permission.
- Pre-commit confirmation is unnecessary; Codex decides and executes.
- Split commits by logical units and use clear messages.
- TODO completion commits must include `ID` in the message (example: `[ID: P0-XXX-01] ...`).

## 5. Implementation and Placement Rules

- Place only language-agnostic code in `src/common/`.
- Place language-specific code in each `py2*.py`, `src/hooks/<lang>/`, `src/profiles/<lang>/`, and `src/runtime/<lang>/pytra/`.
- Do not place files directly under `src/` except transpiler entry points (`py2*.py`).
- Move shared base logic usable across languages (e.g., `CodeEmitter`) to `src/common/`; keep only C++-specific logic in `py2cpp.py`.
- To support future multi-language expansion and avoid `py2cpp.py` bloat, migrate commonizable processing to `src/common/` in phases.
- Consolidate generated-code helper functions in each target runtime (`src/runtime/<lang>/pytra/`) and do not duplicate-embed them into generated code.
- Treat `src/*_module/` as compatibility layers and do not add new runtime implementation files there (planned for gradual removal).
- Treat `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp` as generated from `src/pytra/utils/*.py`; do not edit by hand (auto-updated when running `py2cpp.py`).
- Do not add Python-stdlib-equivalent functionality to `runtime/cpp` (not limited to `json`).
- Keep `src/pytra/std/*.py` as the source of truth for Python-stdlib-equivalent functionality; use transpiled outputs in each target language.
- In selfhost target code (especially `src/pytra/compiler/east.py` family), do not use dynamic imports (`try/except ImportError` fallback or `importlib` lazy import).
- Write imports in statically resolvable form, prioritizing fewer unsupported constructs during self-transpile.
- In transpile-target Python code, direct imports of Python standard modules (`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re`, etc.) are fully prohibited.
- Transpile-target code may import only `src/pytra/std/`, `src/pytra/utils/`, and user-authored `.py` modules.

## 6. Test and Optimization Rules

- Do not modify input cases under `test/fixtures/` for transpiler convenience.
- Do not modify source-of-truth references used for compatibility checks (`materials/`, especially `materials/refs/microgpt/*.py`) for transpiler convenience.
- If derived files are needed for workaround verification, create `work/tmp/*-lite.py` and keep source references unchanged as final evaluation targets.
- Use `-O3 -ffast-math -flto` for C++ in performance comparisons.
- Keep generated artifact directories (`out/`, `test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/`) outside Git management.
- `out/` is for local temporary outputs only; do not place irreproducible source-of-truth data there.
- If `src/pytra/compiler/east_parts/code_emitter.py` is changed, run `test/unit/test_code_emitter.py` first to verify shared utility regressions.
- For `CodeEmitter` / `py2cpp` changes, pass both `python3 tools/check_py2cpp_transpile.py` and `python3 tools/build_selfhost.py` before commit.
- Committing while either of the two commands above fails is prohibited.
- When changing transpiler-related files (`src/py2*.py`, `src/pytra/**`, `src/hooks/**`, `src/profiles/**`), bump the corresponding version in `src/pytra/compiler/transpiler_versions.json` by at least minor and pass `python3 tools/check_transpiler_version_gate.py`.
- For sample regeneration, use `python3 tools/run_regen_on_version_bump.py --verify-cpp-on-diff` to compile/run-check C++ cases that changed after version bump.

## 7. Selfhost Operations Know-How

- Run `python3 tools/prepare_selfhost_source.py` first to inline-expand `CodeEmitter` into `selfhost/py2cpp.py`, then run selfhost transpilation.
- Before selfhost verification, `selfhost/py2cpp.py` and `selfhost/runtime/cpp/*` may be synced to latest `src` (prioritize sync when needed).
- For `#include "runtime/cpp/..."`, headers under `selfhost/` with the same path resolve first. Updating only `src/runtime/cpp` may not fix selfhost build.
- Selfhost build logs may appear on stdout, so collect with `> selfhost/build.all.log 2>&1`.
- In selfhost target code, confirm Python-only expressions do not leak into generated C++ (e.g., `super().__init__`, Python-style inheritance notation).
- On runtime changes, besides `test/unit/test_py2cpp_features.py`, also verify selfhost regeneration and recompilation.
- Even in selfhost-target Python code, direct imports of standard modules are prohibited; use only shim modules in `src/pytra/std/` (e.g., `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.typing`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`).
- In selfhost-critical areas where reliability is prioritized, avoid branches relying on `continue` and literal-set membership like `x in {"a", "b"}`; prefer `if/elif` and explicit comparison (`x == "a" or x == "b"`).
- For daily minimal regression, run `python3 tools/run_local_ci.py` and pass `check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff together.

## 8. External Release Version Operations

- The source of truth for external release version is `docs/VERSION`, using `MAJOR.MINOR.PATCH` (SemVer).
- The current external release version is `0.5.0`.
- `PATCH` updates may be performed by Codex.
- `MAJOR` / `MINOR` updates may be performed only under explicit user instruction.
- `src/pytra/compiler/transpiler_versions.json` is an internal version for regeneration triggers and is managed separately from the external release version (`docs/VERSION`).
