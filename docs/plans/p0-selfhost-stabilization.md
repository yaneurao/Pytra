<a href="../../docs-ja/plans/p0-selfhost-stabilization.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P0-SH

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo.md` `ID: P0-SH-01` to `P0-SH-04`

Background:
- If selfhost transpile/build/run is unstable, the full regression-detection and improvement loop stalls.

Objective:
- Lock selfhost into a minimal path that can be reproduced daily and quickly re-detected when regressions reappear.

In scope:
- Recovery of the selfhost `.py` path
- Stabilization of the `selfhost/py2cpp.out` minimal path
- Stepwise reduction of selfhost compile errors
- Stub cleanup in `tools/prepare_selfhost_source.py`

Out of scope:
- Optimization of non-C++ targets
- Grammar additions unrelated to selfhost

Acceptance criteria:
- Selfhost input/generation/execution is reproducible
- Re-detection procedures remain documented for regressions
- Stub dependency is reduced incrementally

Validation commands:
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`
- `python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py`

Decision log:
- 2026-02-22: Initial draft (split context out of TODO).
- 2026-02-22: Reconfirmed that `build_selfhost` passes, while `check_selfhost_cpp_diff --mode allow-not-implemented` reports `mismatches=3` (`if_else.py`, `01_mandelbrot.py`, `17_monte_carlo_pi.py`). Under `verify_selfhost_end_to_end --skip-build`, only `17_monte_carlo_pi.py` fails by checksum mismatch.
- 2026-02-22: Root-cause investigation showed `selfhost/py2cpp.out` output dropped nested bodies in `if`/`for`, while `PYTHONPATH=src python3 selfhost/py2cpp.py` preserved them. Priority moved to parser/runtime path in the selfhost binary (`core.cpp` lineage).
- 2026-02-22: Corrected root cause to static binding of default `CodeEmitter` `emit_scoped_stmt_list` / `emit_scoped_block` calls in selfhost C++. Added same-name overrides in `src/py2cpp.py` `CppEmitter`, fixing nested-body omission. Verified `failures=0` via `verify_selfhost_end_to_end --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`.
- 2026-02-22: Removed import-resolution table reinitialization from `CppEmitter.__init__`, fixing the route where selfhost C++ failed to resolve `math.*` due to base/derived member separation. Verified `failures=0` on multiple cases and `python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py`.
- 2026-02-22: Removed `dump_codegen_options_text` replacement and `main guard` replacement paths from `tools/prepare_selfhost_source.py`, forwarding canonical `transpile_cli.py` / `py2cpp.py` as-is into selfhost. Confirmed no regressions with `tools/build_selfhost.py`, `./selfhost/py2cpp.out -h`, `--dump-options`, and `verify_selfhost_end_to_end --skip-build`.
- 2026-02-22: Removed exception/help replacement (`_patch_selfhost_exception_paths`) and helper `is_help_requested` from `tools/prepare_selfhost_source.py`, forwarding canonical CLI branches as-is into selfhost. Confirmed no regressions, with `mismatches=3` unchanged in allow-not-implemented mode.
- 2026-02-22: Checked whether `CodeEmitter` hooks no-op replacement can be removed. Without `out = _patch_code_emitter_hooks_for_selfhost(out)`, selfhost C++ fails to compile because `fn(*this, ...)` in `CodeEmitter::hook_on_*` cannot resolve `object` callables. Restored replacement and revalidated stable state.
