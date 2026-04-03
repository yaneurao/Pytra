<a href="../../ja/spec/spec-agent.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Agent Operations Specification (Pytra)

This document defines the operational rules that Codex and Claude Code (collectively "agents") must follow during work.

## 1. Startup Checks

- On startup, agents must first read `docs/ja/spec/index.md` and `docs/ja/todo/index.md`.
- From the incomplete (`[ ]`) items in `docs/ja/todo/index.md`, include any tasks that align with the current request as part of the work scope.

## 1.1 Documentation Language Rules

- Treat `docs/ja/` as the source of truth and update the Japanese version first.
- In normal operation, do not directly edit `docs/en/` (the English version) first — always update `docs/ja/` first.
- User instructions are in Japanese by default; agents operate on the premise that work instructions are given in Japanese.
- `docs/en/` (the English version) may be updated via follow-up translation as needed, and temporary sync lag is acceptable.
- When there are discrepancies between the Japanese and English versions, treat `docs/ja/` as authoritative.
- Adding new files directly under `docs/ja/` (top level) is prohibited in principle; when necessary, an explicit instruction in the same turn is required.
- As an exception, `docs/ja/AGENTS.md` is permanently allowed as the operational bootstrap entry point.
- The root `AGENTS.md` is a local-only pointer (covered by `.gitignore`) and is not managed by Git.
- As an exception, agents may autonomously create new files under `docs/ja/plans/`, `docs/ja/language/`, `docs/ja/todo/archive/`, and `docs/ja/spec/`, within the bounds of the operational rules.

## 2. TODO Execution Rules

- Treat `docs/ja/todo/index.md` as a continuous backlog.
- Only incomplete tasks are kept in `docs/ja/todo/index.md`; sections where all items are complete (`[x]`) are transferred to `docs/ja/todo/archive/index.md` (index) and `docs/ja/todo/archive/YYYYMMDD.md` (content).
- Priority overrides are made via chat instructions specifying `target ID` / `completion criteria` / `exclusions`, not via `docs/ja/todo2.md` (template: `docs/ja/plans/instruction-template.md`).
- Agents for each domain work on their own domain file (`docs/ja/todo/{cpp,go,rust,ts,infra}.md`) in priority order.
- Progress notes in `docs/ja/todo/index.md` should be kept to a single-line summary; detailed decisions and verification logs go in the `Decision Log` of the context file (`docs/ja/plans/*.md`).
- Large tasks may be split into child tasks with the `-S1` / `-S2` format in the context file.
- If uncommitted changes remain due to interruption, complete the same `ID` or revert the changes before moving to a different `ID`.
- Update the check state when a task is completed.

## 3. Documentation Sync Rules

- When specifications change, features are added, or procedures are updated, update `README.md` as necessary.
- Check the consistency of documents linked from `README.md` (`docs/ja/tutorial/README.md`, `sample/README-ja.md`, `docs/ja/spec/index.md`, `docs/ja/plans/pytra-wip.md`, `docs/ja/spec/spec-philosophy.md`) and update them simultaneously if needed.
- Not leaving implementation-documentation discrepancies is a required completion condition for changes.
- When adding, deleting, or renaming scripts in `tools/`, update `docs/ja/spec/spec-tools.md` simultaneously.
- The "Update History" in `docs/ja/README.md` retains only the latest 3 entries; full history is recorded in `docs/ja/changelog.md`.
- Terminology rule: when referring to type annotations, always write "type annotation" (not just "annotation").
- Writing rule: when describing features or folder structure, always state the purpose (what it is for).
- Writing rule: describe not only "where to place things" but also "why there", to prevent mixing of `std` and `tra` responsibilities.
- `docs/ja/spec/` contains only current specifications; retired specifications are moved to `docs/ja/spec/archive/YYYYMMDD-<slug>.md`.
- `docs/ja/spec/archive/index.md` is maintained as an index of old specifications; add a link each time an archive is added.

## 4. Commit Rules

- Agents may commit without asking for user permission each time, once the work is logically complete.
- There is no need to ask "may I commit?" before committing; agents make that judgment themselves.
- Split commits into logical units and include a message that clearly conveys the intent of the change.
- TODO-completion commits must include the `ID` in the message (e.g., `[ID: P0-XXX-01] ...`).

## 4.1 Prohibited Git Operations (Multi-Instance Environment)

Because multiple agent instances (Codex / Claude Code) operate simultaneously on the same working tree, the following git operations that would destroy uncommitted changes of other instances are **prohibited**.

- `git stash` — stashes all uncommitted changes, rolling back other instances' work
- `git checkout -- <file>` — discards uncommitted changes to a file
- `git restore <file>` — same as above (new syntax for `checkout --`)
- `git reset --hard` — discards all changes
- `git clean -f` — deletes untracked files

Alternatives:
- To undo changes, manually revert using Edit/Write, or check the diff with `git diff <file>` before acting.
- If temporary stashing is necessary, copy the file to `/tmp/` and restore manually.

## 5. Implementation and Placement Rules

- `src/toolchain/emit/common/` contains only language-agnostic code.
- Language-specific code goes in the respective `py2*.py`, `src/toolchain/emit/<lang>/`, `src/toolchain/emit/<lang>/profiles/`, and `src/runtime/<lang>/{generated,native}/`. The `pytra-gen/pytra-core` for unmigrated backends is treated only as temporary debt.
- Only the transpiler entry points (`py2*.py`) are placed directly under `src/`.
- Base logic shareable across all languages, such as `CodeEmitter`, is consolidated in `src/toolchain/emit/common/`; only C++-specific logic remains in `py2cpp.py`.
- In anticipation of future multi-language expansion and to prevent `py2cpp.py` from becoming bloated, shareable processing is incrementally migrated to `src/toolchain/emit/common/`.
- Helper functions for generated code are consolidated in the canonical runtime lane for each target language (migrated backends: `src/runtime/<lang>/{generated,native}/`) and are not duplicated in generated code.
- `src/*_module/` is treated as a compatibility layer; no new runtime entity files are added (slated for phased removal).
- `src/runtime/cpp/generated/utils/png.cpp` / `src/runtime/cpp/generated/utils/gif.cpp` are treated as generated artifacts from `src/pytra/utils/*.py` and must not be edited by hand (auto-updated when `py2cpp.py` runs).
- The png/gif output implementations in `src/runtime/<lang>/generated/` must be generated solely from `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` as their source of truth; hand-written per-language implementations are prohibited.
- **The source-of-truth files `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` / `src/pytra/std/*.py` must not be modified by language backend owners.** Changes to these source-of-truth files propagate to all languages, so changes must be made by the planner or infrastructure owner after confirming the impact on all languages.
- The only permitted language-specific differences in png/gif are input/output adapters and minimal runtime glue code; the core encoding logic (CRC32/Adler32/DEFLATE/LZW/chunk construction) must not be duplicated by hand.
- The image runtime enforces the same separation of responsibilities across all languages as in C++. The canonical form is: handwritten runtime in `src/runtime/<lang>/native/`, and only artifacts generated from `src/pytra/utils/{png,gif}.py` in `src/runtime/<lang>/generated/`. The unmigrated backend `pytra-core/pytra-gen` is only allowed as rollout debt.
- PNG/GIF encoding bodies (`write_rgb_png` / `save_gif` / `grayscale_palette`) must not be written directly into core-side files like `py_runtime.*`. If needed, only a thin delegation to the canonical generated lane API is allowed.
- Generated image runtime artifacts must include a traceable marker for their source and generation pipeline (e.g., `source: src/pytra/utils/png.py`, `source: src/pytra/utils/gif.py`, `generated-by: ...`).
- Python standard library equivalent functionality must not be additionally implemented on the `runtime/cpp` side — not just for `json`, but for anything.
- The source of truth for Python standard library equivalent functionality is always `src/pytra/std/*.py`; each target language uses the transpile result thereof.
- In selfhost target code (especially `src/toolchain/misc/east.py` and related), do not use dynamic imports (`try/except ImportError` fallback, lazy imports via `importlib`).
- Write imports in a form that can be statically resolved, and prioritize not introducing unsupported syntax during self-transpilation.
- In selfhost target code (`src/` transpiler bodies, backends, and IR implementations), dependency on the Python standard `ast` module (`import ast` / `from ast ...`) is prohibited.
- If `ast`-based analysis is needed, use EAST node traversal or existing selfhost-compatible parser/IR information instead.
- Exception: inspection and test code in `tools/` and `test/` is not selfhost target code, so `ast` usage is permitted there.
- In Python code intended for transpilation, direct `import` of Python standard modules (`json`, `pathlib`, `sys`, `os`, `glob`, `argparse`, `re`, etc.) is prohibited.
- As an exception, `typing` (`import typing`, `from typing import ...`) is allowed as an annotation-only no-op import.
- As an exception, `dataclasses` (`import dataclasses`, `from dataclasses import ...`) is allowed as a decorator-resolution-only no-op import.
- Transpile-target code may only import from `src/pytra/std/`, `src/pytra/utils/` modules, and user-created `.py` modules.

## 6. Testing and Optimization Rules

- Do not modify input cases in `test/fixtures/` to suit the transpiler.
- Do not alter the reference materials used for compatibility verification (`materials/` directory, especially `materials/refs/microgpt/*.py`) to suit the transpiler.
- If a derived file is needed for transpilation-avoidance verification, create it as `work/tmp/*-lite.py` and keep the original as the evaluation standard (the ultimate target to pass).
- Use `-O3 -ffast-math -flto` for C++ when comparing execution speed.
- Generated artifact directories (`out/`, `work/transpile/obj/`, `work/transpile/cpp2/`, `sample/obj/`, `sample/out/`) are kept out of Git management.
- **Temporary output to the following is prohibited**: `out/`, `selfhost/`, `sample/obj/`, `/tmp/`.
  - Temporary output from builds, transpilation, and verification should go in `work/tmp/`.
  - Output from selfhost tests should go in `work/selfhost/`.
  - `out/` / `selfhost/` / `sample/obj/` are legacy compatibility directories and must not be used as new output destinations. They carry a risk of conflicts between multiple instances.
  - `sample/out/` is exclusively for sample/py output examples (PNG/GIF/TXT). Output for other purposes (transpile results, temporary files, etc.) is prohibited.
  - `/tmp/` is a system-shared area where garbage accumulates without cleanup. Its use is prohibited.
  - `tempfile.TemporaryDirectory()` also uses `/tmp/` and is therefore prohibited. Instead, create a subdirectory under `work/tmp/`.
- When modifying `src/toolchain/emit/common/emitter/code_emitter.py`, always run `tools/unittest/common/test_code_emitter.py` first to check for common utility regressions.
- For `CodeEmitter` / `py2cpp` changes, pass at minimum both `python3 tools/check/check_py2cpp_transpile.py` and `python3 tools/build_selfhost.py` before committing.
- Committing while either of the two commands above is failing is prohibited.
- The internal version gate (`transpiler_versions.json`) is obsolete. Verify changes via parity check.
- For ad-hoc C++ compilation experiments (for debugging/investigation), place the source and artifacts under `/tmp/` or `work/tmp/` rather than in the repository root (see the `tempfile.TemporaryDirectory()` pattern).
- GCC dump flags (e.g., `-fdump-tree-all`) output to the current directory; do not use them in the repository root. If needed, explicitly specify `-dumpdir /tmp/`.
- After compilation experiments, run `git status --short` to verify that no unintended artifacts remain in the repository root.

## 7. Selfhost Operational Know-How

- Run `python3 tools/prepare_selfhost_source.py` first to create a self-contained source with `CodeEmitter` inlined into `work/selfhost/py2cpp.py`, then perform the selfhost transpilation.
- Before selfhost verification, `work/selfhost/py2cpp.py` and `work/selfhost/runtime/cpp/*` may be synced to the latest `src` (sync takes priority when needed).
- `#include "runtime/cpp/..."` resolves headers under `work/selfhost/` first. Updating only `src/runtime/cpp` may not fix a selfhost build.
- The selfhost build log may appear on `stdout`, so use `> work/selfhost/build.all.log 2>&1` to capture it all.
- For selfhost target code, confirm that Python-specific expressions do not leak into the generated C++ (e.g., `super().__init__`, Python-style inheritance notation).
- When changing the runtime, in addition to running `tools/unittest/emit/cpp/test_py2cpp_features.py` for regression, also check the selfhost regeneration and recompilation results.
- Even in selfhost target Python code, direct imports of standard modules are prohibited; use only the shims in `src/pytra/std/` (e.g., `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`). Only `typing` is allowed as a direct import, as an annotation-only no-op.
- In sections of selfhost code where reliability takes priority, avoid branching that relies on `continue` and literal set membership like `x in {"a", "b"}`; prefer `if/elif` with explicit comparisons (`x == "a" or x == "b"`).
- The daily minimum regression is `python3 tools/run/run_local_ci.py`, which runs `check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff together.

## 8. Public Release Version Management

- The source of truth for public release versions is `docs/VERSION`, using `MAJOR.MINOR.PATCH` (SemVer) format.
- The current public release version is `0.7.0`.
- Agents may update `PATCH` on their own.
- `MAJOR` / `MINOR` updates require an explicit instruction from the user.
- The internal version gate (`transpiler_versions.json`) is obsolete. Only the public release version (`docs/VERSION`) is managed.
