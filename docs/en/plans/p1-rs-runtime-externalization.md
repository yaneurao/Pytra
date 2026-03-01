# P1: Rust Runtime Externalization (Remove Inline Helpers / Embedded `mod pytra`)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-RS-RUNTIME-EXT-01` in `docs/ja/todo/index.md`

Background:
- Current Rust generated code (e.g., `sample/rs/01_mandelbrot.rs`) inlines `py_*` helper groups and `mod pytra { ... }`.
- Inline expansion is convenient for single-file execution but leads to generated-code bloat, runtime duplication, and missed runtime updates.
- Runtime source files such as `src/runtime/rs/pytra/built_in/py_runtime.rs` already exist, but `py2rs.py` currently outputs only a single `.rs` file and has no runtime-placement path.

Objective:
- Remove inline runtime/helper bodies from Rust backend generated code and unify on external runtime references.
- Consolidate runtime source of truth under `src/runtime/rs/pytra/`, and have emitter focus only on call generation.

Scope:
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/py2rs.py`
- `src/runtime/rs/pytra/` (including missing helper/API additions)
- `test/unit/test_py2rs_smoke.py`
- `tools/check_py2rs_transpile.py`
- `tools/runtime_parity_check.py` (Rust path)
- `tools/regenerate_samples.py` and `sample/rs` regeneration

Out of scope:
- Rust backend performance optimizations (clone reduction, parenthesis reduction, etc.)
- Redesign of `isinstance/type_id` semantics
- Adding Cargo project generation

Acceptance Criteria:
- `py2rs` output does not inline runtime/helper bodies (`fn py_perf_counter`, `fn py_isdigit`, `mod pytra { ... }`, etc.).
- Generated code can build/run by referencing external runtime files.
- `check_py2rs_transpile` / Rust smoke / parity (minimum `sample/18`, in principle `--all-samples`) pass without regression.
- After regenerating `sample/rs`, confirm zero inline helper residue.

Validation Commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs rs --force`
- `rg -n "fn py_perf_counter|fn py_isdigit|mod pytra \\{" sample/rs`

## Breakdown

- [x] [ID: P1-RS-RUNTIME-EXT-01-S1-01] Finalize inventory of Rust emitter inline helper outputs and API mapping against source-of-truth `src/runtime/rs/pytra`.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S1-02] Finalize runtime-reference contract for Rust artifacts (`mod/use` structure and output-dir placement) and document fail-closed conditions.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S2-01] Fill missing helpers/APIs in `src/runtime/rs/pytra` to provide semantics equivalent to inline implementations.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S2-02] Add runtime-file placement path in `py2rs.py`, moving generated code to a state where external runtime is resolvable.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S2-03] Remove runtime/helper body emission from `rs_emitter.py` and switch to runtime API calls only.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S3-01] Update `check_py2rs_transpile` / Rust smoke / parity and lock regressions.
- [x] [ID: P1-RS-RUNTIME-EXT-01-S3-02] Regenerate `sample/rs` and confirm zero inline helper residue.

## S1-01 Inventory Results (inline helpers vs runtime source of truth)

### A. `RUST_RUNTIME_SUPPORT` (fixed string in `rs_emitter.py`)

- Inline outputs:
  - `py_perf_counter`, `py_isdigit`, `py_isalpha`, `py_str_at`, `py_slice_str`
  - PNG/GIF group: `py_write_rgb_png`, `py_save_gif` and helper functions
  - `mod time`, `mod math`, `mod pytra` (re-export of `pytra::runtime::{png,gif}` and `pytra::utils`)
- Mapping vs `src/runtime/rs/pytra/built_in/py_runtime.rs`:
  - Existing implementations: `py_isdigit`, `py_isalpha`, `py_write_rgb_png`, `py_save_gif`, `perf_counter`
  - Naming gap: `py_perf_counter` (inline) vs `perf_counter` (runtime)
  - Missing functionality: `py_str_at`, `py_slice_str`, public modules for `mod time/math/pytra`

### B. `_emit_pyany_runtime` (dynamic output only when needed)

- Inline outputs:
  - `enum PyAny`
  - Conversion helpers: `py_any_to_i64`, `py_any_to_f64`, `py_any_to_bool`, `py_any_to_string`, `py_any_as_dict`
  - Helper trait groups (`PyAnyTo*Arg`)
- Runtime source-of-truth status:
  - Not implemented in `src/runtime/rs/pytra/built_in/py_runtime.rs` (full gap).

### C. `_emit_isinstance_runtime_helpers` (dynamic output only when needed)

- Inline outputs:
  - `PYTRA_TID_*` constants
  - `PyTypeInfo`, `py_type_info`
  - `PyRuntimeTypeId` trait
  - `py_runtime_type_id`, `py_is_subtype`, `py_issubclass`, `py_isinstance`
- Runtime source-of-truth status:
  - Not implemented in `src/runtime/rs/pytra/built_in/py_runtime.rs` (full gap).

### D. Missing APIs to fill in S2 (final)

- Target file: `src/runtime/rs/pytra/built_in/py_runtime.rs`
- Additions:
  - `py_str_at`, `py_slice_str`
  - `pub mod time`, `pub mod math`, `pub mod pytra`
  - `PyAny` and full `py_any_*` set
  - full `type_id/isinstance` set (`PYTRA_TID_*`, `PyRuntimeTypeId`, `py_isinstance`, etc.)

## S1-02 Runtime Reference Mode (Contract)

### Generated artifact layout

- On `py2rs.py` output, always place `py_runtime.rs` in the same directory as the target `.rs` file.
- Declare the following at the top of the generated main file:
  - `mod py_runtime;`
  - `pub use crate::py_runtime::{math, pytra, time};`
  - `use crate::py_runtime::*;`

### Reference rules

- Keep existing import lowerings (`use crate::time::perf_counter;`, `use crate::pytra::runtime::png;`) and preserve backward compatibility via `pub use`.
- Emitter does not output runtime helper bodies; only helper calls.
- Emitter may reference only identifiers published by runtime source of truth.

### fail-closed conditions

- If runtime source `py_runtime.rs` is missing, `py2rs.py` fails immediately with `RuntimeError`.
- If runtime placement to output target fails, treat process as failed even after writing main `.rs` (do not tolerate partial generation).
- If unit/smoke detects inline residues such as `fn py_perf_counter` or `mod pytra {`, treat as failure.

Decision Log:
- 2026-02-28: Per user instruction, helper/runtime separation for Rust was newly filed as P1.
- 2026-03-01: Ran inventory of `RUST_RUNTIME_SUPPORT`/`_emit_pyany_runtime`/`_emit_isinstance_runtime_helpers` and fixed migration targets/missing APIs for `py_runtime.rs` (`S1-01`).
- 2026-03-01: Finalized generation-time runtime placement contract (`mod py_runtime;` + `pub use` + `use crate::py_runtime::*;`) and fail-closed conditions (`S1-02`).
- 2026-03-01: Added `py_str_at`/`py_slice_str`, `PyAny` conversions, `type_id/isinstance` base, and `pub mod time/math/pytra` to `src/runtime/rs/pytra/built_in/py_runtime.rs`; validated standalone syntax via `rustc --crate-type lib` (`S2-01`).
- 2026-03-01: Added bundled `py_runtime.rs` copy path to `py2rs.py` and verified runtime placement at generation target via CLI smoke (`S2-02`). Four failures in `check_py2rs_transpile.py` (`Try/Yield/Swap` unsupported) are existing spec gaps handled in `S3-01`.
- 2026-03-01: Removed runtime inline output (`RUST_RUNTIME_SUPPORT`/`_emit_pyany_runtime`/`_emit_isinstance_runtime_helpers` calls) from `rs_emitter.py`, migrated to `mod py_runtime;` + `pub use` + `use crate::py_runtime::*;`, and switched `isinstance` to runtime-side type-table initialization via `py_register_generated_type_info()` (`S2-03`).
- 2026-03-01: Confirmed `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v` (28 OK), `python3 tools/check_py2rs_transpile.py` (`checked=129 ok=129 fail=0 skipped=10`), and `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout` (18/18 PASS) (`S3-01`).
- 2026-03-01: After `python3 tools/regenerate_samples.py --langs rs --force` (`regen=18 fail=0`), confirmed zero inline helper residue with `rg -n "fn py_perf_counter|fn py_isdigit|mod pytra \\{" sample/rs --glob '!py_runtime.rs'` (`S3-02`).
