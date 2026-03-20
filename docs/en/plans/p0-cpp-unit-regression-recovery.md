# P0: Root-Fix C++ Unit Regressions (Normalize SoT/IR/Emitter/Runtime Contracts)

Last updated: 2026-03-06

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-REGRESSION-RECOVERY-01`

Background:
- As of 2026-03-06, the C++ backend already passed parity for all 18 `sample` cases and the `test/fixtures` parity suite.
- However, `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py` was still red, with failures concentrated in the following areas.
  - generated runtime breakage: `json_extended_runtime`, `argparse_extended_runtime`
  - import/include and runtime-module resolution breakage: `from_pytra_runtime_import_{png,gif}`, `from_pytra_std_{time,pathlib}`, `import_includes_are_deduped_and_sorted`, `os_glob_extended_runtime`, `os_path_calls_use_runtime_helpers`
  - container / iterator / comprehension semantics breakage: `dict_get_items_runtime`, `any_dict_items_runtime`, `comprehension_dict_set_runtime`
  - emitter / CLI contract breakage: `mod_mode_native_and_python`, `cli_dump_options_allows_planned_bigint_preset`, `cli_reports_user_syntax_error_category`, `emit_stmt_*`
- `tools/build_multi_cpp.py` and the fixture compile helper had already been corrected to compile only runtime `.cpp` files that were actually included. At that point, the remaining failures were real C++ transpiler/runtime contract bugs, not false positives caused by unrelated runtime sources being dragged into the build.
- Hand-editing `.gen.*` at that point would only break again on regeneration, so every fix had to go back to one of the actual ownership layers: the SoT (`src/pytra/*`), IR/lowering, the emitter, or the runtime-generation contract.

Goal:
- Converge the C++ backend unit regressions by restoring the natural responsibility boundaries of the transpiler instead of shipping ad-hoc patches.
- Eliminate breakage in generated runtimes, import resolution, container semantics, and CLI contracts, with guard coverage that prevents recurrence.

Scope:
- `src/pytra/{built_in,std,utils}/`
- `src/toolchain/emit/cpp/`
- import/runtime resolution under `src/toolchain/`
- `tools/build_multi_cpp.py`
- `tools/gen_makefile_from_manifest.py`
- `test/unit/toolchain/emit/cpp/`

Out of scope:
- fixes for non-C++ backends
- benchmark work
- temporary survival patches through handwritten `.gen.*` edits
- adding new runtime APIs

Acceptance criteria:
- `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py` passes.
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` passes.
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` passes.
- `.gen.*` around `json/argparse/png/gif/time/pathlib/os/glob` regenerate correctly from SoT and do not depend on handwritten edits to generated artifacts.
- The C++ emitter does not gain new ad-hoc handwritten branches for import-source module names or runtime helper names.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_py2cpp_features.py -k json_extended_runtime`
- `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_py2cpp_features.py -k argparse_extended_runtime`

## Breakdown

- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01] Root-fix the C++ unit regressions in the order of SoT/IR/Emitter/Runtime contracts and re-green both the unit suite and fixture/sample parity.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S1-01] Reclassify the failing tests into `generated runtime`, `import/include resolution`, `container semantics`, and `emitter/CLI contracts`, and fix the ownership layer for each repair.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-01] Fix the `json` generated-runtime breakage through SoT and C++ runtime-generation contract changes (no handwritten `.gen.*` edits).
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S2-02] Fix the `argparse` generated-runtime breakage through SoT changes, reserved-name avoidance, and class/member emission contract changes.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-01] Fix import resolution, include dedupe/sort, and one-to-one module include contracts for `pytra.utils.{png,gif}` and `pytra.std.{time,pathlib}`.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S3-02] Return `os.path` / `glob` runtime-helper routing to owner/module-metadata-based resolution and reduce C++ emitter special cases.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-01] Fix container-view and iterator semantics for `dict.items()` / `dict.get()` / `any()` / dict/set comprehensions by aligning built-in SoT and runtime adapters.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S4-02] Clean up the C++ emitter contracts around `mod_mode`, statement-dispatch fallback, and CLI `dump-options` / error-category handling, and fix option reflection and diagnostic consistency.
- [x] [ID: P0-CPP-REGRESSION-RECOVERY-01-S5-01] Rerun the full C++ unit suite, fixture parity, and sample parity, confirm that no regressions remain, and update `docs/ja/todo`.

Decision log:
- 2026-03-06: Confirmed that `tools/runtime_parity_check.py --targets cpp --case-root fixture` and `--case-root sample --all-samples` were already green, while `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py` was not. From that point onward, the repair scope was limited to real failures in the unit suite.
- 2026-03-06: `build_multi_cpp.py` and the fixture compile helper had already been fixed to compile only runtime sources that were actually included, so the `json.gen.*` / `argparse.gen.*` compile failures were treated as generation-contract breakage rather than build-path false positives.
- 2026-03-06: This plan explicitly forbade direct edits to `.gen.*`. Every fix had to be made only after identifying the broken ownership layer among SoT, IR/lowering, the emitter, and runtime generation.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S1-01`] Classified the active failures from `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_*.py` by comparing the full failing set against targeted reruns of representative tests. Ownership was fixed as follows.
  - generated runtime / SoT + generation contract:
    - `test_json_extended_runtime`
      - `json.gen.h/.cpp` failed to compile because of broken string escaping, duplicated namespaces, and misplaced member definitions.
      - Ownership: `src/pytra/std/json.py` and the C++ class/function emission contract.
    - `test_argparse_extended_runtime`
      - Compile failure because of the `default` reserved-word collision, undeclared members, unresolved `setattr` / `SystemExit`, and broken `optional<list<str>>` rendering.
      - Ownership: `src/pytra/std/argparse.py`, reserved-name avoidance, and the class/member emission contract.
  - import/include resolution:
    - `test_import_includes_are_deduped_and_sorted`
    - `test_from_pytra_runtime_import_png_emits_one_to_one_include`
    - `test_from_pytra_runtime_import_gif_emits_one_to_one_include`
    - `test_from_pytra_std_time_import_perf_counter_resolves`
    - `test_from_pytra_std_pathlib_import_path_resolves`
      - The current output still emitted direct `runtime/cpp/...*.gen.h` paths instead of `pytra/...` public includes, violating the one-to-one import/include contract.
      - Ownership: the C++ include emitter that assembles public includes from resolved import metadata.
  - owner/module metadata resolution:
    - `test_os_path_calls_use_runtime_helpers`
    - `test_os_glob_extended_runtime`
      - `os.path` was rendered directly as `pytra::std::os_path::*` helpers instead of `py_os_path_*`, and `os_glob_extended` also failed to compile because the namespace path was unresolved.
      - Ownership: routing through `runtime_module_id/runtime_symbol` and owner metadata for `os.path` / `glob`.
  - container / iterator semantics:
    - `test_dict_get_items_runtime`
      - Runtime failure with `string index out of range`. The likely cause was a broken runtime adapter on the `dict.items()` / tuple path.
    - `test_any_dict_items_runtime`
      - `dict_get_str(...)` overload resolution was ambiguous between `dict<str, object>` and `optional<dict<str, object>>`.
    - `test_comprehension_dict_set_runtime`
      - `py_dict_get(even_map, 2)` on `dict<int64, int64>` failed overload resolution because the literal type did not match the declared key type.
      - Ownership: runtime adapters / typed helper contracts around `dict.items/get` and comprehension paths.
  - emitter / CLI contracts:
    - `test_mod_mode_native_and_python`
      - `%=` was broken into a standalone `a % b;` expression instead of `a %= b;`.
    - `test_cli_reports_user_syntax_error_category`
      - The self-hosted parser's `unsupported_syntax` was still surfacing directly as `[not_implemented]` instead of being normalized to `[user_syntax_error]`.
    - `test_cli_dump_options_allows_planned_bigint_preset`
      - `--dump-options` was not dumping options and instead fell through into multi-file generation.
    - `test_emit_stmt_dispatch_table_handles_continue_and_unknown`
      - Unknown statements raised `RuntimeError` instead of going through the comment fallback.
    - `test_emit_stmt_fallback_works_when_dynamic_hooks_disabled`
      - `Pass` was collapsing into a bare `;` instead of `/* pass */`.
      - Ownership: statement-emitter fallback behavior, compound-assignment emission, CLI option dispatch, and error-category normalization.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-01`] `json` was broken by four separate generation-contract failures. 1) Class splitting used a raw `count("{")-count("}")` heuristic and mis-split `_JsonParser` method blocks when string literals contained `"{"` or `"}"`, so `_brace_delta_ignoring_literals()` was introduced to fix brace counting in split/class extraction/namespace scans. 2) The C-style string-literal escape path did not handle `\\b` / `\\f`, so control characters were being emitted raw; escaping was added consistently to the common path, the C++ header path, and the runtime emit path. 3) The runtime public header omitted default arguments, so `json.dumps(...)` calls failed to compile; `build_cpp_header_from_east()` was updated to emit default arguments on function declarations. 4) A runtime-emit-specific post-process was added to strip default arguments from top-level function definitions in `.cpp`, so the definitions no longer duplicated those defaults. `src/pytra/std/json.py` itself was not edited; `src/runtime/cpp/std/json.gen.*` changed only through regeneration. Verification: `python3 -m py_compile ...code_emitter.py ...cli.py ...header_builder.py`, `python3 src/py2x.py --target cpp src/pytra/std/json.py --emit-runtime-cpp`, and `test_json_extended_runtime` passed compile/run.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S2-02`] `argparse` was broken across three layers. 1) Keyword arguments for imported runtime class methods (`ArgumentParser.add_argument`) were being lowered into positional C++ calls without filling intermediate defaults, so arguments like `choices=` and `default=` shifted into the wrong positional slots. To fix that, SoT-derived class-method `arg_defaults` metadata was preserved, and the call emitter now inserts the default nodes before assembling the positional C++ call. 2) `argparse.py` itself used shapes that were hostile to the current C++ runtime contract, such as `Optional[list[str]]` and `dict[str, _ArgSpec]`, so `description/action/help` were normalized to value-type defaults, `argv` was moved to an object input path, `by_name` was simplified to `dict[str, int64]`, and `choices` was moved back to an empty-list default. 3) The C++ default-argument renderer still could not emit empty `list/dict/set` literals in either headers or emitter output, so support was added for `list[...] {}`, `dict[...] {}`, and `set[...] {}`. Verification: `python3 -m py_compile ...call.py ...module.py ...cpp_emitter.py ...header_builder.py ...argparse.py`, `python3 src/py2x.py --target cpp src/pytra/std/argparse.py --emit-runtime-cpp`, and `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p test_py2cpp_features.py -k argparse_extended_runtime` all passed.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S3-01`] The import/include contract was broken because `runtime_symbol_index` still returned internal headers such as `src/runtime/cpp/std/*.gen.h` as public headers, and the emitter then emitted `#include "runtime/cpp/...gen.h"` directly. The fix had four parts. 1) Added public-include conversion to `runtime_paths.py` (`pytra/std/time.h`, `pytra/utils/png.h`, and similar) so includes are normalized onto the public shim headers under `src/runtime/cpp/...`. 2) Updated `emit-runtime-cpp` so it also generates forwarder headers under `src/runtime/cpp/pytra/.../*.h`. 3) Updated `tools/gen_runtime_symbol_index.py` so C++ adopts the shim headers as `public_headers`. 4) Regenerated the `png/gif/time/pathlib` runtime modules and updated `runtime_symbol_index.json`. Verification: `python3 tools/gen_runtime_symbol_index.py --check` and the five tests `test_from_pytra_runtime_import_{png,gif}_emits_one_to_one_include`, `test_from_pytra_std_{time,pathlib}_import_*`, and `test_import_includes_are_deduped_and_sorted` all passed.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S3-02`] `os.path` was broken in two layers. 1) `src/pytra/std/os.py` no longer bound the `path` submodule as the Python fallback, so it had diverged from the SoT contract (`from pytra.std import os_path as path`). 2) The C++ side rendered `os.path.*` directly as `pytra::std::os_path::*`, but helper declarations/definitions and public-shim/source tracking were not aligned. The fix restored `os_path as path` in `os.py`, reorganized `runtime_calls.json` so `os.path` and `pytra.std.os_path` route through `py_os_path_*` helpers while the owner is still `pytra::std::os_path`, added `src/runtime/cpp/std/os_path.ext.h` to separate helper declarations, added wrapper implementations in `os_path.ext.cpp`, taught `CppModuleEmitter._collect_runtime_modules_from_node()` to collect real runtime modules from module-attribute nodes (here `pytra.std.os_path`), and updated `tools/cpp_runtime_deps.py` so `RUNTIME_ROOT` includes the public shim headers under `src/runtime/cpp/pytra/*.h`. Finally, `--emit-runtime-cpp` regenerated `os.py`, `os_path.py`, and `glob.py`, and `src/toolchain/emit/cpp/cli.py` was updated so the public shim also forwards `.ext.h`. Verification: `test_os_path_calls_use_runtime_helpers`, `test_os_glob_extended_runtime`, `test_pylib_os_glob.py`, and `python3 tools/gen_runtime_symbol_index.py --check` all passed.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S4-01`] Fixed three breakage families together. 1) Object-owner `dict.items()` cases such as `table.get(..., {}).items()` must not be treated as identical to typed dict iteration, so the C++ emitter was extended with the condition that `DictItems` switches over to the `py_dict_items(...)` adapter path. For `dict.get`-immediately-followed cases where the type falls to `unknown`, the builtin runtime path was reinforced so it rechecks the value type of the `dict.get` owner and still selects `py_dict_items`. 2) On `dict[str, object]`, `dict_get_str(root, "name", "")` was ambiguously convertible to both the `object` overload and the `optional<dict<...>>` overload, so `py_runtime.ext.h` gained direct plain-dict overloads `dict_get_{bool,str,int,float,list}` for `dict<str, object>`. 3) The subscript `even_map[2]` on `dict<int64, int64>` was lowered with the C++ literal `2` as `int`, which broke template deduction against `K=int64`, so `_coerce_dict_key_expr()` was updated to coerce numeric constant keys into the declared key type. Verification: `test_dict_get_items_runtime`, `test_any_dict_items_runtime`, `test_comprehension_dict_set_runtime`, and the seven `dict.get`-related cases in `test_py2cpp_codegen_issues.py` all passed.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S4-02`] Fixed the emitter / CLI contract breakage. 1) `DEFAULT_AUG_OPS["Mod"]` incorrectly held `%`, which broke native `%=`; it was corrected to `%=`. 2) `emit_stmt()` had a fallback table but still threw immediately on unknown statements; it now emits `/* unsupported stmt kind: ... */` when dynamic hooks are disabled, and `Pass` is unified to `/* pass */` across profiles. 3) In `src/toolchain/emit/cpp/cli.py`, `--dump-options` had been accidentally nested under a compatibility branch for `.cpp` output, so it was moved back to an early return after input validation. 4) In `src/toolchain/frontends/transpile_cli.py`, self-hosted-parser token mismatches such as `unsupported_syntax: expected token ...` had been treated as `not_implemented`; they are now normalized to `user_syntax_error`. 5) At the same time, old output-contract assumptions in `test/unit/toolchain/emit/cpp` were updated to the current output contract, covering public shim includes, typed-list/value-class output, lowering for `super()` / `Base.f(self, ...)`, and negative constants like `-(1)` / `-(2)`. Verification: the five known cases in `test_py2cpp_features.py`, plus `test_cpp_runtime_symbol_index_integration.py`, `test_cpp_type.py`, `test_east3_cpp_bridge.py`, and the fail-fast tracking cases in `test_py2cpp_codegen_issues.py`, all passed.
- 2026-03-06: [ID: `P0-CPP-REGRESSION-RECOVERY-01-S5-01`] `python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_*.py'` passed all 484 tests. In addition, `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture` passed with `pass=3 fail=0`, and `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` passed with `pass=18 fail=0`, including reconfirmed sample artifact `size/CRC32` matches. The final follow-up changes included `typing.*` annotation normalization, synchronized mutable-parameter contracts in runtime headers, elimination of `py_runtime_argv_storage` TU splitting, cleanup of the `transpile_cli` compatibility shim wrapper, and regeneration of the `random/re/math` runtime modules.
