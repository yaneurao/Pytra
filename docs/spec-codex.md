# Codex Operation Specification (Pytra)

<a href="../docs-jp/spec-codex.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


This document defines operation rules that Codex follows while working.

## 1. Startup Checks

- At Codex startup, first check `docs-jp/spec.md` and `docs-jp/todo.md`.
- From unfinished (`[ ]`) items in `docs-jp/todo.md`, include tasks aligned with the current request as work targets.

## 1.1 Documentation Language Policy

- Treat `docs-jp/` as the source of truth and update Japanese docs first.
- Assume user instructions are primarily in Japanese and operate with Japanese instructions as the default workflow.
- `docs/` (English docs) may be updated later as delayed translation when needed.
- If Japanese and English documentation diverge, prioritize `docs-jp/` as canonical.

## 2. TODO Execution Rules

- Treat `docs-jp/todo.md` as a continuous backlog.
- Keep only unfinished tasks in `docs-jp/todo.md`. When a section is fully complete (all items `[x]`), move it to `docs-jp/todo-old.md`.
- Execute unfinished items sequentially in priority order.
- Update check status when tasks are completed.

## 3. Documentation Sync Rules

- On spec changes, feature additions, or procedure changes, update `README.md` as needed.
- Check consistency of documents linked from `README.md` (`docs/how-to-use.md`, `docs/sample-code.md`, `docs/spec.md`, `docs/pytra-readme.md`) and their canonical Japanese sources (`docs-jp/how-to-use.md`, `docs-jp/sample-code.md`, `docs-jp/spec.md`, `docs-jp/pytra-readme.md`), and update them together when needed.
- Include "no implementation-doc mismatch left" in change completion criteria.
- If scripts in `tools/` are added/removed/renamed, update `docs/tools.md` and `docs-jp/tools.md` at the same time.
- Terminology rule: when referring to type annotations, always write "type annotation" (not just "annotation").
- Writing rule: when describing features or folder structures, always state the purpose (what they are for).
- Writing rule: write not only "where to place" but also "why place there," to prevent responsibility mixing between `std` and `tra`.

## 4. Commit Operations

- When work content is logically coherent, commits may be made without per-commit user permission.
- Pre-commit confirmation ("is it okay to commit?") is unnecessary; Codex decides and executes.
- Split commits by logical unit and use messages that make intent clear.

## 5. Implementation and Placement Rules

- Place only language-independent code in `src/common/`.
- Place language-specific code in each `py2*.py` or each `*_module/`.
- Do not place anything under `src/` root except transpiler entry points (`py2*.py`).
- Move shared base logic usable across all languages (e.g., `CodeEmitter`) into `src/common/`, leaving only C++-specific logic in `py2cpp.py`.
- To support future multi-language expansion and avoid `py2cpp.py` bloat, incrementally migrate commonizable processing into `src/common/`.
- Aggregate helper functions for generated code in each target runtime (`src/*_module/`) and do not embed duplicates into generated code.
- Treat `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp` as generated from `src/pytra/utils/*.py`; do not edit by hand (auto-updated during `py2cpp.py` execution).
- Do not add Python-standard-library-equivalent implementations on `runtime/cpp` side (not limited to `json`).
- Keep `src/pytra/std/*.py` as the source of truth for Python-standard-library-equivalent functionality, and use transpiled outputs in each target language.
- In selfhost target code (especially `src/pytra/compiler/east.py` related), do not use dynamic imports (`try/except ImportError` fallback or `importlib` lazy import).
- Write imports in statically resolvable form, prioritizing avoidance of unsupported syntax increase during self-transpilation.
- In transpilation target Python code, direct imports of Python standard modules (`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re`, etc.) are fully prohibited.
- Transpilation target code may import only modules in `src/pytra/std/`, `src/pytra/utils/`, and user-authored `.py` modules.

## 6. Test and Optimization Rules

- Do not modify input cases in `test/fixtures/` for transpiler convenience.
- Use `-O3 -ffast-math -flto` for C++ in performance comparisons.
- Keep generated artifact directories (`test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/`) out of Git.
- If `src/pytra/compiler/east_parts/code_emitter.py` is changed, always run `test/unit/test_code_emitter.py` first to verify shared utility regressions.
- For `CodeEmitter` / `py2cpp` changes, at minimum pass both `python3 tools/check_py2cpp_transpile.py` and `python3 tools/build_selfhost.py` before commit.
- Committing while either command above is failing is prohibited.

## 7. Selfhost Operation Know-How

- Run `python3 tools/prepare_selfhost_source.py` first to inline-expand `CodeEmitter` into `selfhost/py2cpp.py`, then run selfhost transpilation.
- Before selfhost verification, `selfhost/py2cpp.py` and `selfhost/runtime/cpp/*` may be synced to latest `src` (prioritize sync when needed).
- For `#include "runtime/cpp/..."`, headers under `selfhost/` with the same path resolve first. Updating only `src/runtime/cpp` may not fix selfhost build.
- Selfhost build logs may appear on `stdout`, so collect with `> selfhost/build.all.log 2>&1`.
- In selfhost target code, verify that Python-only expressions do not leak into generated C++ (e.g., `super().__init__`, Python-style inheritance notation).
- On runtime changes, in addition to running regressions in `test/unit/test_py2cpp_features.py`, also verify selfhost regeneration and recompilation results.
- Even in selfhost target Python code, direct import of standard modules is prohibited; use only shims in `src/pytra/std/` (e.g., `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.typing`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`).
- In selfhost-critical areas where robustness is prioritized, avoid branches relying on `continue` and literal-set membership like `x in {"a", "b"}`; prefer `if/elif` and explicit comparisons (`x == "a" or x == "b"`).
- For daily minimal regression, run `python3 tools/run_local_ci.py` and pass `check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff together.
