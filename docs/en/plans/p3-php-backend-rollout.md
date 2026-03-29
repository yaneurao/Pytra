<a href="../../ja/plans/p3-php-backend-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P3: Add PHP Backend (EAST3 -> Native PHP)

Last updated: 2026-03-02

Related TODO:
- `ID: P3-PHP-BACKEND-01` in `docs/ja/todo/index.md`

Background:
- The agreed implementation order for new languages was `Ruby -> Lua -> PHP`, and backend paths for Ruby/Lua are already in place.
- At this point, PHP is still unsupported as a conversion target language and is absent from `py2<lang>` multi-language operations.
- Existing policy is to generate native code directly from `EAST3` to each language, not via sidecar.

Goal:
- Add a native conversion path `EAST3 -> PHP` with `py2php.py` as entrypoint.
- Operate runtime helpers via separated PHP runtime files, not inline embedding in generated code.
- Establish baseline transpile/parity paths for `sample/` and `test/fixtures`.

Scope:
- `src/py2php.py` (new)
- `src/hooks/php/emitter/` (new)
- `src/runtime/php/pytra/` (new runtime)
- `tools/check/check_py2php_transpile.py` (new)
- `tools/check/runtime_parity_check.py` (add PHP target)
- `tools/gen/regenerate_samples.py` (add php output path)
- `sample/php/*` (regeneration)
- `tools/unittest/test_py2php_smoke.py` (new)
- `docs/ja/how-to-use.md` / `docs/ja/spec/spec-user.md` (add guidance)

Out of scope:
- Self-hosting of PHP backend (managed as separate P4 task)
- Advanced optimization (EAST3 optimizer strengthening handled separately)
- Frontend expansion (inputs other than Python)

Specification scope (fixed in S1-01):
- Supported syntax (v1):
  - Statements: `Assign/AnnAssign/Expr/Return/If/While/ForCore(RuntimeIter, StaticRange)/Break/Continue/Pass`
  - Expressions: `Name/Constant/BinOp/UnaryOp/Compare/BoolOp/Call/Attribute/Subscript/List/Dict/Tuple/IfExp`
  - Declarations: `FunctionDef/ClassDef` (single inheritance only)
  - Containers: represent `list/dict/tuple/bytes/bytearray` as PHP arrays + helpers
  - Built-ins: `len/int/float/bool/str/min/max/isinstance/print/range/enumerate`
- Unsupported (fail-closed):
  - `Yield/Await/Try/With/Lambda/Match`, multiple inheritance, generator expressions, variable keyword expansion
  - On unsupported node detection, emitter throws `RuntimeError` and disallows partial generation
- Compatibility policy:
  - No EAST2 compatibility; only `--east-stage 3`
  - Unknown-type expressions fall back to `mixed`-equivalent helper paths, prioritizing known-type paths

Runtime separation contract (fixed in S1-01):
- Generated code header references `require_once __DIR__ . "/pytra/py_runtime.php";`.
- Helper bodies are not embedded into generated `.php` (import only).
- Runtime placement:
  - `src/runtime/php/pytra/py_runtime.php` (common helpers)
  - `src/runtime/php/pytra/utils/png.php` / `gif.php` (I/O helpers)
  - `src/runtime/php/pytra/std/*.php` (`time`, `math`, `pathlib`)
- `tools/gen/regenerate_samples.py` synchronizes copy of `sample/php/pytra/**` when generating samples.
- Keep helper-name semantics aligned across all backends (e.g., `py_truthy`, `py_len`, `py_str`).

Acceptance criteria:
- `src/py2php.py` can generate PHP from EAST3 input.
- Generated code is executable with runtime separation style (`require` / `include`).
- `check_py2php_transpile.py` stably passes for `test/fixtures`.
- `sample/php` is regenerated and parity passes for representative cases (at least `01/03/06/16/18`).
- Docs reflect PHP backend usage and constraints.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v`
- `python3 tools/check/check_py2php_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs php --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --ignore-unstable-stdout 01_mandelbrot 03_julia_set 06_julia_parameter_sweep 16_glass_sculpture_chaos 18_parser_combinator`

Decision log:
- 2026-03-02: Based on user direction, planned PHP support as `P3` and filed it as the next phase in the `Ruby -> Lua -> PHP` sequence.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S1-01] Finalized v1 scope. Documented supported syntax, unsupported syntax, and runtime separation contract in this plan, and fixed policy to handle unsupported items fail-closed (stop by exception).
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S1-02] Added `src/py2php.py` and `hooks/php/emitter`, creating a new CLI path that loads EAST3 via `load_east3_document(target_lang="php")`. Connected runtime by copying to `output/pytra/py_runtime.php`.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-01] Extended `php_native_emitter` to output `FunctionDef/If/While/ForCore(StaticRange, RuntimeIter)` and basic expressions (constant/binary/compare/call/container). Verified conversion of `core/add`, `control/if_else`, `control/for_range` with `py2php`, confirming for-range outputs as PHP `for`.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-02] Added `ClassDef` output (`extends`, `__construct`, `parent::method`) and lowerings for `isinstance`/`dict.get`/`Unbox`. Verified conversion of `oop/inheritance.py`, `oop/inheritance_virtual_dispatch_multilang.py`, `oop/is_instance.py`, and `sample/py/18_mini_language_interpreter.py`, confirming class/container path generation issues were resolved.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-03] Split runtime into `src/runtime/php/pytra/{py_runtime.php,runtime/{png,gif}.php,std/time.php}` and extended `py2php.py` to sync-copy into `output/pytra/**`. Unified emitter structure to reference `__pytra_perf_counter/__pytra_len/__pytra_str_*` with no helper-body embedding into generated code.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-01] Added `tools/unittest/test_py2php_smoke.py` (11 cases) and `tools/check/check_py2php_transpile.py`. Confirmed pass for both `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v` and `python3 tools/check/check_py2php_transpile.py`.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-02] Added `php` target to `tools/gen/regenerate_samples.py` and `tools/check/runtime_parity_check.py`, and registered `php` version token in `transpiler_versions.json`. Regenerated 18 outputs under `sample/php` with `python3 tools/gen/regenerate_samples.py --langs php --force`; `runtime_parity_check --targets php` in this environment was confirmed up to `toolchain_missing` skip because PHP toolchain is not installed.
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-03] Updated doc paths. Added `py2php` and `work/transpile/php` / `sample/php` placement notes to `docs/{ja,en}/spec/spec-user.md`; added PHP run procedure and regression commands to `docs/{ja,en}/how-to-use.md`; reflected PHP link in sample-conversion code lists in `README.md` / `docs/ja/README.md`.

## Breakdown

- [x] [ID: P3-PHP-BACKEND-01-S1-01] Finalize PHP backend scope (supported/unsupported syntax and runtime separation contract).
- [x] [ID: P3-PHP-BACKEND-01-S1-02] Add `src/py2php.py` and profile loader to establish CLI path.
- [x] [ID: P3-PHP-BACKEND-01-S2-01] Implement PHP native emitter skeleton and pass output for functions/branches/loops/basic expressions.
- [x] [ID: P3-PHP-BACKEND-01-S2-02] Implement minimum lowerings for class/inheritance and container operations (`list/dict/tuple` equivalents).
- [x] [ID: P3-PHP-BACKEND-01-S2-03] Separate runtime helpers into `src/runtime/php/pytra/` and unify generated-code references to that layout.
- [x] [ID: P3-PHP-BACKEND-01-S3-01] Add `test_py2php_smoke.py` and `check_py2php_transpile.py` to establish regression detection paths.
- [x] [ID: P3-PHP-BACKEND-01-S3-02] Integrate PHP into `runtime_parity_check` and `regenerate_samples`, then regenerate `sample/php`.
- [x] [ID: P3-PHP-BACKEND-01-S3-03] Update PHP backend descriptions in docs (`how-to-use/spec/README`) and lock usage paths.
