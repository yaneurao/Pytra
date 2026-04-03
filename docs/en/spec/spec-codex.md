<a href="../../ja/spec/spec-codex.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Operations Specification for Codex (Pytra) — Former Name

> **This file uses the former name. The canonical document has moved to [spec-agent.md](./spec-agent.md).**

This document defines the operational rules Codex must follow while working on this repository.

## 1. Startup checks

- At startup, Codex first checks `docs/ja/spec/index.md` and `docs/ja/todo/index.md`.
- From the unfinished items, `[ ]`, in `docs/ja/todo/index.md`, Codex includes tasks that are consistent with the current request.

## 1.1 Document-language operation rules

- Treat `docs/ja/` as the source of truth and update the Japanese version first.
- In normal operation, do not edit `docs/en/`, the English version, first. Update `docs/ja/` first.
- User instructions are assumed to be primarily in Japanese, and Codex operates on that basis.
- `docs/en/`, the English version, may be updated later as a follow-up translation, and temporary delay in synchronization is acceptable.
- If the Japanese and English versions differ, judge based on the contents of `docs/ja/`.
- Adding a new file directly under the top level of `docs/ja/` is prohibited by default. If it is necessary, an explicit instruction in the same turn is required.
- As an exception, `docs/ja/AGENTS.md` is permanently allowed as the operational bootstrap entry.
- The root `AGENTS.md` is a local-only pointer, ignored by `.gitignore`, and is not tracked in Git.
- As exceptions, Codex may autonomously create new files under `docs/ja/plans/`, `docs/ja/language/`, `docs/ja/todo/archive/`, and `docs/ja/spec/`, as long as the normal operation rules are followed.

## 2. TODO execution rules

- Treat `docs/ja/todo/index.md` as the continuous backlog.
- Keep only unfinished tasks in `docs/ja/todo/index.md`. When a whole section is complete, all items are `[x]`, move it to `docs/ja/todo/archive/index.md`, the index, and `docs/ja/todo/archive/YYYYMMDD.md`, the full body.
- Do not use `docs/ja/todo2.md` to override priority. Instead, override it in chat by explicitly specifying `target ID`, `done criteria`, and `out of scope`, using `docs/ja/plans/instruction-template.md` as the template.
- Execute unfinished items in priority order, the smallest `P<number>` first, and within the same priority use the first item from the top.
- If even one `P0` task remains unfinished, do not start `P1` or below unless there is an explicit override instruction.
- Keep progress notes in `docs/ja/todo/index.md` to one-line summaries. Write detailed decisions and verification logs into the `Decision log` of the context file under `docs/ja/plans/*.md`.
- Large tasks may be split into child tasks of the form `-S1` and `-S2` in context files. `tools/check/check_todo_priority.py` allows the top unfinished `ID` and its child `ID`s.
- In any turn that adds progress logs to `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, pass `python3 tools/check/check_todo_priority.py`. On the `plans` side, only date lines inside `Decision log` count as progress entries.
- If uncommitted diffs remain due to interruption or similar causes, either finish the same `ID` or revert those diffs before moving to another `ID`.
- Update the checklist state when a task is completed.

## 3. Documentation synchronization rules

- Update `README.md` as needed when specifications, features, or procedures change.
- Check consistency for the documents linked from `README.md`, `docs/ja/tutorial/README.md`, `sample/README-ja.md`, `docs/ja/spec/index.md`, `docs/ja/plans/pytra-wip.md`, and `docs/ja/spec/spec-philosophy.md`, and update them together if needed.
- The completion criteria must include leaving no mismatch between implementation and documentation.
- If a script under `tools/` is added, removed, or renamed, update `docs/ja/spec/spec-tools.md` in the same turn.
- Keep only the latest three items in the update history of `docs/ja/README.md`, and record the full history in `docs/ja/changelog.md`.
- Terminology rule: when referring to a type annotation, always write `type annotation`, not just `annotation`.
- Writing rule: when describing a feature or a folder structure, always state what it is for.
- Writing rule: state not only where something belongs but also why it belongs there, so responsibilities between `std` and `tra` do not get mixed.
- Keep only current specifications directly under `docs/ja/spec/`, and move retired specifications to `docs/ja/spec/archive/YYYYMMDD-<slug>.md`.
- Maintain `docs/ja/spec/archive/index.md` as the index of old specifications and append links whenever a new archive entry is added.

## 4. Commit operations

- When the work has reached a logically coherent unit, Codex may commit without asking the user each time.
- No pre-commit confirmation is required. Codex decides on its own.
- Split commits by logical units and use messages that make the intent of the change clear.
- Commits that complete TODO work must include the `ID` in the message, for example `[ID: P0-XXX-01] ...`.

## 4.1 Prohibited git operations in a multi-instance environment

Because multiple Codex and Claude Code instances may run simultaneously in the same working tree, the following git operations are prohibited because they can destroy uncommitted changes from other instances.

- `git stash`, because it shelves all uncommitted changes and can roll back another instance's work
- `git checkout -- <file>`, because it discards uncommitted changes in a file
- `git restore <file>`, same effect as above
- `git reset --hard`, because it discards all changes
- `git clean -f`, because it deletes untracked files

Alternatives:

- If you need to undo changes, restore them manually by editing or writing, or inspect the diff first with `git diff <file>`.
- If you need temporary safekeeping, copy the file to `/tmp/` and restore it manually later.

## 5. Implementation and placement rules

- Place only language-independent code in `src/toolchain/emit/common/`.
- Place language-specific code in each `py2*.py`, `src/toolchain/emit/<lang>/`, `src/toolchain/emit/<lang>/profiles/`, and `src/runtime/<lang>/{generated,native}/`. The legacy `pytra-gen/pytra-core` layout in not-yet-migrated backends is only rollout debt.
- Do not place anything directly under `src/` except the transpiler entrypoints, `py2*.py`.
- Shared base logic usable across all languages, such as `CodeEmitter`, belongs under `src/toolchain/emit/common/`, while `py2cpp.py` should keep only C++-specific logic.
- To avoid `py2cpp.py` becoming too large as multi-language support expands, migrate any commonizable processing gradually into `src/toolchain/emit/common/`.
- Consolidate generated-code helper functions in the canonical runtime lane for each target language, `src/runtime/<lang>/{generated,native}/` on migrated backends, and do not duplicate-embed them into generated code.
- Treat `src/*_module/` as compatibility layers and do not add new runtime implementation files there.
- Treat `src/runtime/cpp/generated/utils/png.cpp` and `src/runtime/cpp/generated/utils/gif.cpp` as generated outputs from `src/pytra/utils/*.py`, and never edit them by hand. They are updated automatically when `py2cpp.py` runs.
- Under `src/runtime/<lang>/generated/`, allow only SoT-derived generated implementations of PNG and GIF writing from `src/pytra/utils/png.py` and `src/pytra/utils/gif.py`. Handwritten per-language implementations are forbidden.
- The only allowed language-specific differences around PNG and GIF are thin I/O adapters and minimal runtime-connection code. Do not hand-copy the core encoding logic, CRC32, Adler32, DEFLATE, LZW, or chunk construction.
- Enforce the same runtime separation as C++ across all languages. The canonical form is handwritten runtime in `src/runtime/<lang>/native/` and only outputs derived from `src/pytra/utils/{png,gif}.py` in `src/runtime/<lang>/generated/`. Legacy `pytra-core/pytra-gen` is allowed only as rollout debt.
- Do not hard-code PNG or GIF encoder bodies, `write_rgb_png`, `save_gif`, `grayscale_palette`, into core-side files such as `py_runtime.*`. Only thin delegation to canonical generated-lane APIs is allowed.
- Generated-lane image-runtime artifacts must contain markers that identify their origin and generation path, for example `source: src/pytra/utils/png.py`, `source: src/pytra/utils/gif.py`, and `generated-by: ...`.
- Do not implement Python-standard-library-equivalent functionality on the `runtime/cpp` side, not only `json` but everything of that class.
- The source of truth for Python-standard-library-equivalent functionality is always `src/pytra/std/*.py`, and each target language must use the transpiled result.
- In selfhost-target code, especially the `src/toolchain/misc/east.py` family, do not use dynamic imports, such as `try/except ImportError` fallback or lazy imports via `importlib`.
- Write imports in statically resolvable form, prioritizing compatibility with self-transpilation over unsupported dynamic patterns.
- In selfhost-target code, the transpiler itself, backend code, and IR implementation under `src/`, dependence on the Python standard `ast` module, `import ast` or `from ast ...`, is prohibited.
- If AST-like analysis is needed, use EAST-node traversal or existing selfhost-compatible parser and IR data instead.
- Exception: check and test code under `tools/` and `test/` is not a selfhost target, so using `ast` there is allowed.
- In Python code that is itself subject to transpilation, direct import of standard modules such as `json`, `pathlib`, `sys`, `os`, `glob`, `argparse`, and `re` is prohibited.
- Exception: `typing`, `import typing`, `from typing import ...`, is allowed as an annotation-only no-op import.
- Exception: `dataclasses`, `import dataclasses`, `from dataclasses import ...`, is allowed as a decorator-resolution-only no-op import.
- Code subject to transpilation may import only modules under `src/pytra/std/`, `src/pytra/utils/`, and user-authored `.py` modules.

## 6. Test and optimization rules

- Do not modify input cases under `test/fixtures/` merely for the convenience of the transpiler.
- Do not modify the original reference sources used for compatibility checks under `materials/`, especially `materials/refs/microgpt/*.py`, merely for transpiler convenience.
- If a derived file is needed to verify a workaround, create it separately as `work/tmp/*-lite.py` and keep the original source as the final evaluation target.
- Use `-O3 -ffast-math -flto` for C++ in runtime-speed comparisons.
- Keep generated artifact directories, `out/`, `work/transpile/obj/`, `work/transpile/cpp2/`, `sample/obj/`, and `sample/out/`, outside Git.
- Temporary output is forbidden in `out/`, `selfhost/`, `sample/obj/`, and `/tmp/`.
- Use `work/tmp/` for build, transpile, and verification temporary outputs.
- Use `work/selfhost/` for selfhost-test outputs.
- `out/`, `selfhost/`, and `sample/obj/` are legacy compatibility directories and must not be used as new output destinations. They create conflict risks across multiple instances.
- `sample/out/` is reserved for sample output examples, PNG, GIF, and TXT, and must not be used for transpile output or temporary files.
- `/tmp/` is a system-shared area that accumulates garbage and is therefore prohibited.
- `tempfile.TemporaryDirectory()` is also prohibited because it uses `/tmp/`. Create subdirectories under `work/tmp/` instead.
- If `src/toolchain/emit/common/emitter/code_emitter.py` changes, run `tools/unittest/common/test_code_emitter.py` first to verify common-utility regressions.
- For `CodeEmitter` and `py2cpp` changes, at minimum both `python3 tools/check/check_py2cpp_transpile.py` and `python3 tools/build_selfhost.py` must pass before commit.
- Committing while either of those two commands is failing is prohibited.
- When changing transpiler-related files, `src/py2*.py`, `src/pytra/**`, `src/toolchain/emit/**`, or `src/toolchain/emit/**/profiles/**`, update the corresponding version in `src/toolchain/misc/transpiler_versions.json` by at least a minor bump and pass `python3 tools/check/check_transpiler_version_gate.py`.
- Use `python3 tools/run/run_regen_on_version_bump.py --verify-cpp-on-diff` for sample regeneration, and compile/run-check any C++ cases that changed due to the version bump.
- For ad hoc C++ compile experiments, debugging or investigation, put both source and artifacts under `work/tmp/`, not in the repository root.
- GCC dump flags such as `-fdump-tree-all` write into the current directory, so do not use them in the repository root. If necessary, specify `-dumpdir /tmp/`.
- After any experiment involving compilation, confirm with `git status --short` that no unintended generated files remain in the repository root.

## 7. Selfhost operating know-how

- Run `python3 tools/prepare_selfhost_source.py` first, generating a self-contained source with `CodeEmitter` inlined into `work/selfhost/py2cpp.py`, and then run the selfhost transpilation.
- Before selfhost verification, `work/selfhost/py2cpp.py` and `work/selfhost/runtime/cpp/*` may be synchronized to the latest `src`, and synchronization should be prioritized when needed.
- For `#include "runtime/cpp/..."`, headers under `work/selfhost/` take precedence if they share the same name. Updating only `src/runtime/cpp` may therefore fail to fix the selfhost build.
- Because selfhost build logs may appear on stdout, capture them together with `> work/selfhost/build.all.log 2>&1`.
- In selfhost-target code, confirm that Python-only constructs do not leak into generated C++, for example `super().__init__` or Python-style inheritance syntax.
- When runtime changes are made, verify not only `tools/unittest/emit/cpp/test_py2cpp_features.py` but also selfhost regeneration and recompilation.
- Even for Python code that is a selfhost target, direct standard-library imports are prohibited. Use only shim modules under `src/pytra/std/`, for example `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, and `pytra.std.re`. Only `typing` may still be imported directly as an annotation-only no-op import.
- In selfhost-critical areas where reliability has priority, avoid branches that depend on `continue` or literal-set membership such as `x in {"a", "b"}`. Prefer `if/elif` and explicit comparisons such as `x == "a" or x == "b"`.
- For the daily minimum regression set, run `python3 tools/run/run_local_ci.py` and pass `check_py2cpp_transpile`, unit tests, selfhost build, and selfhost diff together.

## 8. External release-version operation

- The source of truth for the external release version is `docs/VERSION`, and the format is `MAJOR.MINOR.PATCH`, SemVer.
- The current external release version is `0.7.0`.
- Codex may update `PATCH`.
- Codex may update `MAJOR` or `MINOR` only under explicit user instruction.
- `src/toolchain/misc/transpiler_versions.json` is an internal regeneration-trigger version and is managed separately from the external release version in `docs/VERSION`.
