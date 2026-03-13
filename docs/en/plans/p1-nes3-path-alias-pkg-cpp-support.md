# P1: align cross-module `pytra.std.pathlib.Path` alias reuse with the C++ multi-file contract

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-PATH-ALIAS-PKG-CPP-01`

Background:
- The Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/path_alias_pkg/`](../../../materials/refs/from-Pytra-NES3/path_alias_pkg) re-exports `Path` from `.compat` and reuses it from `.entry`.
- As of 2026-03-13, the generated C++ declares only `make_path` in `compat.h`, while `entry.cpp` tries to call a nonexistent `pytra_mod_compat::Path(raw)`.
- This is not a `Path` runtime problem. It is a residual where an alias/type symbol reused through another module is misclassified as a value call.

Objective:
- Resolve `from .compat import Path` through the type/alias lane in the C++ multi-file path instead of lowering it to a nonexistent module function call.
- Lock representative reuse of std type symbols re-exported by user modules.

In scope:
- Classification and C++ name rendering for cross-module imported alias/type symbols
- Multi-file compile smoke for `materials/refs/from-Pytra-NES3/path_alias_pkg/`
- Regression, docs, and TODO sync for the path-alias residual

Out of scope:
- New `Path` runtime APIs
- A full redesign for aliases of every built-in type
- Non-C++ backends

Acceptance criteria:
- The generated C++ for `path_alias_pkg` compiles.
- The consumer module stops emitting nonexistent calls such as `pytra_mod_compat::Path(...)`.
- The representative reuse lane for `Path` re-exported through a user module is locked in regressions.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/path_alias_pkg/entry.py --target cpp --output-dir /tmp/pytra_nes3_path_alias_pkg`
- `for f in /tmp/pytra_nes3_path_alias_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_path_alias_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## Breakdown

- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S1-01] Lock the current compile failure and alias/type misclassification residual in focused regressions, the plan, and TODO.
- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S2-01] Fix symbol classification and rendering so cross-module `Path` aliases resolve through the type/constructor lane.
- [ ] [ID: P1-NES3-PATH-ALIAS-PKG-CPP-01-S3-01] Sync multi-file compile smoke and docs wording to the current contract.

Decision log:
- 2026-03-13: Opened as a separate task because this is about cross-module alias reuse, not the already-fixed `Path` stringify lane.
