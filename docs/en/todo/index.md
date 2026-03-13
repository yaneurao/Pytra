# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-14

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details such as decisions and verification logs must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file, but keep the parent checkbox open until the parent `ID` is completed.
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` or one of its child IDs.
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` or `/tmp` only when necessary, and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P0

- [ ] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01] relative wildcard import native backend rollout
  Context: [p0-relative-wildcard-import-native-rollout.md](../plans/p0-relative-wildcard-import-native-rollout.md)
  Progress memo: `S2-03` makes `lua/php/ruby` green on the module-graph bundle transpile smoke lane while keeping the single-file direct lane fail-closed for wildcard imports. Next is syncing coverage / parity docs to the final state.

### P1

1. [ ] [ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01] Stop lowering `NotImplementedError` to an undefined C++ symbol and make `not_implemented_error.py` compile.
Context: [docs/en/plans/p1-nes3-not-implemented-error-cpp-support.md](../plans/p1-nes3-not-implemented-error-cpp-support.md)
- Progress memo: Not started.

2. [ ] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01] Remove the `!bytes` residual for member-based `bytes` truthiness and make `cartridge_like.py` compile.
Context: [docs/en/plans/p1-nes3-bytes-member-truthiness-cpp-support.md](../plans/p1-nes3-bytes-member-truthiness-cpp-support.md)
- Progress memo: Not started.

3. [ ] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01] Align the `rc<list<T>>` lane for `field(default_factory=lambda: [0] * N)` and make `list_default_factory.py` compile.
Context: [docs/en/plans/p1-nes3-list-default-factory-rc-list-cpp-support.md](../plans/p1-nes3-list-default-factory-rc-list-cpp-support.md)
- Progress memo: Not started.

4. [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01] Align cross-module `pytra.std.pathlib.Path` alias reuse with the C++ multi-file contract and make `path_alias_pkg` compile.
Context: [docs/en/plans/p1-nes3-path-alias-pkg-cpp-support.md](../plans/p1-nes3-path-alias-pkg-cpp-support.md)
- Progress memo: Not started.

5. [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01] Align header ordering and reference lanes for imported classes that use module constants and make `apu_const_pkg` compile.
Context: [docs/en/plans/p1-nes3-apu-const-pkg-cpp-support.md](../plans/p1-nes3-apu-const-pkg-cpp-support.md)
- Progress memo: Not started.

6. [ ] [ID: P1-NES3-BUS-PORT-PKG-CPP-01] Align header/symbol qualification plus parameter passing for imported bus types and make `bus_port_pkg` compile.
Context: [docs/en/plans/p1-nes3-bus-port-pkg-cpp-support.md](../plans/p1-nes3-bus-port-pkg-cpp-support.md)
- Progress memo: Not started.

### P2

1. [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01] Fully retire the deleted `src/runtime/cpp/core/**` compatibility surface from live-tree assumptions and reduce it to guard-only references.
Context: [docs/en/plans/p2-cpp-legacy-core-compat-retire.md](../plans/p2-cpp-legacy-core-compat-retire.md)
- Progress memo: Not started.

2. [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01] Rework the `@extern` runtime/emitter contract across all languages so it uses native owners plus generic extern metadata instead of generated rewrites.
Context: [docs/en/plans/p2-multilang-extern-runtime-realign.md](../plans/p2-multilang-extern-runtime-realign.md)
- Progress memo: Not started.

3. [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01] Introduce a bundle-based coverage matrix and fix `feature x lane x backend` contract coverage at 100% as a surface separate from the support matrix.
Context: [docs/en/plans/p2-backend-contract-coverage-100.md](../plans/p2-backend-contract-coverage-100.md)
- Progress memo: Not started.

4. [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01] Push typed fallback out of `py_runtime.h` and back into EAST3, the C++ emitter, and runtime SoT so the header shrinks without physical splitting.
Context: [docs/en/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md](../plans/p2-cpp-pyruntime-upstream-fallback-shrink.md)
- Progress memo: Not started.
