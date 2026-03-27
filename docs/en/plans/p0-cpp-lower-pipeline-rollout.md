<a href="../../ja/plans/p0-cpp-lower-pipeline-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: C++ Three-Stage Migration (Option 1: `CppLower` / `CppIrOptimizer` / `CppEmitter`)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-CPP-LOWER-PIPELINE-01` in `docs/ja/todo/index.md`

Background:
- The current C++ backend is centered on `EAST3 -> (EAST3 optimization) -> CppEmitter`, leaving C++-specific structural decisions in the emitter.
- Existing `CppOptimizer` passes operate directly on EAST3 nodes, and the C++ backend-specific IR boundary (post-lowering responsibility) is not explicit.
- By user agreement, we will migrate only C++ first using Option 1 (`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`) in phased steps.

Goal:
- Split C++ backend responsibilities into `EAST3 -> CppLower -> CppIrOptimizer -> CppEmitter`, fixing boundaries between semantic decisions, normalization, and syntax rendering.
- Reduce `CppEmitter` to a deterministic renderer of C++ IR, and gradually remove direct EAST3 interpretation logic.

In scope:
- `src/toolchain/emit/cpp/lower/cpp_lower.py` (new)
- `src/toolchain/emit/cpp/optimizer/cpp_ir_optimizer.py` (new; bridge from existing optimizer)
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` (responsibility reduction)
- `src/py2cpp.py` (new pipeline wiring)
- C++ backend regression tests (unit / transpile / sample)

Out of scope:
- Simultaneous rollout to other backends such as Rust/Scala/Go
- EAST2/EAST1 spec changes
- Semantic changes to the C++ runtime API

Acceptance criteria:
- During `py2cpp`, processing always runs in order: `CppLower -> CppIrOptimizer -> CppEmitter`.
- In migrated areas of `CppEmitter`, dependence on EAST3 `kind` branching is removed and unified as C++ IR node rendering.
- Existing C++ transpile regressions (`tools/check_py2cpp_transpile.py`) pass with no regressions.
- Regenerated C++ for `sample/01,08,18` keeps compilability and parity.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_*lower*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

## Breakdown

- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-01] Define the minimal C++ IR node set (Stmt/Expr/Type/Decl) and fail-closed contract.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-02] Fix file responsibilities and public APIs for Option 1 (`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`).
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-01] Add `cpp_lower.py` and implement a skeleton lowering path from EAST3 Module to C++ IR Module.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-02] Add `cpp_ir_optimizer.py` and implement migration/rewiring strategy for existing optimizer passes.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-03] Add pipeline wiring and dump/trace entry points from `py2cpp`.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-01] Move statement-level structural decisions (loop/if/tuple unpack, etc.) from emitter to lower/optimizer.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-02] Move expression-level normalization (cast/compare/binop redundancy removal) from emitter to lower/optimizer.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-03] Reduce direct EAST3 branching in `CppEmitter` and converge on C++ IR renderer responsibility.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-01] Add unit tests validating lower/optimizer/emitter boundaries and lock in regressions.
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-02] Run C++ transpile/sample/parity checks and verify no regressions.

Decision log:
- 2026-03-02: Per user direction, filed Option 1 (`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`) as P0 with C++-first rollout and other languages deferred.
- 2026-03-02: Introduced `CppLower` as `pass_through_v0` (preserve EAST3 shape). Enforced fail-closed contract requiring root `dict` + `kind=Module`.
- 2026-03-02: Introduced `CppIrOptimizer` as a thin delegation layer to existing `optimize_cpp_ir`; rewired `emit_cpp_from_east` to `lower -> optimizer -> emitter`.
- 2026-03-02: `dump_cpp_opt_trace` now concatenates `cpp_lower_trace` and existing `cpp_optimizer_trace` into one file (CLI compatibility maintained).
- 2026-03-02: Added `CppBraceOmitHintPass`, converting brace-omission decisions for `If/ForCore` etc. into optimizer-side `cpp_omit_braces_v1` hints. Updated emitter to prefer hints (partial start of S3-01).
- 2026-03-02: Added `CppForIterModeHintPass`, moving legacy `For` `iter_mode` decisions to optimizer-side `cpp_iter_mode_v1` hints. Current `pyobj` list model decision remains in emitter.
- 2026-03-02: Added `CppCastCallNormalizePass`, collapsing nested `py_to_*` and duplicate casts in `static_cast` + `py_to_*` at optimizer side (partial start of S3-02).
- 2026-03-02: Added `CppCompareNormalizePass`, normalizing `bool_expr == True/False` / `!= True/False` into `bool_expr` / `!bool_expr` to reduce compare redundancy in optimizer (partial start of S3-02).
- 2026-03-02: Added `CppBinOpNormalizePass`, collapsing redundant numeric binops (`+0/-0/*1`) in optimizer. Marked S3-02 (cast/compare/binop) complete.
- 2026-03-02: Added `CppForcoreDirectUnpackHintPass`, moving `ForCore` tuple-target `direct_unpack` decisions to optimizer hints. Together with `CppBraceOmitHintPass` / `CppForIterModeHintPass`, marked S3-01 (loop/if/tuple unpack) complete.
- 2026-03-02: `CppLower` now annotates statement nodes with `cpp_stmt_kind_v1`; `CppEmitter.emit_stmt` updated to hint-first dispatch. Started S3-03 reduction of direct EAST3 raw-kind references (incomplete at that point).
- 2026-03-02: `CppLower` also annotates expression nodes with `cpp_expr_kind_v1`; `CppEmitter.render_expr` migrated to hint-first dispatch. Refactored `_emit_stmt_kind_fallback` to table-driven form and marked S3-03 complete.
- 2026-03-02: Added boundary tests in `test_cpp_optimizer.py` for `CppLower` / `CppIrOptimizer` / `emit_cpp_from_east` integration and locked unit regressions (S4-01).
- 2026-03-02: Verified no regressions with `tools/check_py2cpp_transpile.py` (136/136 pass, skip6), `tools/regenerate_samples.py --langs cpp --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`, and `tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot 08_langtons_ant 18_mini_language_interpreter --ignore-unstable-stdout` (3/3 pass) (S4-02).

## C++ IR v0 Contract (S1-01)

- The root must be a `dict` with required `kind == "Module"`.
- `body` allows the existing EAST3-compatible statement node set (including `Stmt/Expr/Decl/Type`), and phase 1 does not alter shape.
- If lower/optimizer input violates the contract, fail closed with `RuntimeError`.
- Only a C++ IR root (`Module`) is passed to `CppEmitter`.

## API Boundaries (S1-02)

- `toolchain.emit.cpp.lower.cpp_lower.CppLower.lower(east_module, debug_flags=...) -> (cpp_ir, report)`
- `toolchain.emit.cpp.lower.cpp_lower.lower_cpp_from_east3(...)` is a convenience wrapper around the above.
- `toolchain.emit.cpp.optimizer.cpp_ir_optimizer.CppIrOptimizer.optimize(cpp_ir, ...) -> (cpp_ir, report)`
- `toolchain.emit.cpp.optimizer.cpp_ir_optimizer.optimize_cpp_ir_module(...)` is a convenience wrapper around the above.
- `toolchain.emit.cpp.emitter.cpp_emitter.emit_cpp_from_east(...)` remains the public bridge and runs `lower -> optimizer -> CppEmitter.transpile()`.
