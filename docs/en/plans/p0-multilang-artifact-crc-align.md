<a href="../../ja/plans/p0-multilang-artifact-crc-align.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Align Sample Artifact CRC (Remove Kotlin Gate + Revalidate Swift + Repair Fail Groups)

Last updated: 2026-03-04

Related TODO:
- `ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01` in `docs/ja/todo/index.md`

Background:
- Artifact CRC32 comparison has already been added to `tools/check/runtime_parity_check.py` (CRC32 is checked in addition to size).
- Kotlin explicitly skipped artifact comparison with `ignore_artifacts=True`, so it was incomplete as a comparison target.
- In response to the revalidation request for `PyPy..Kotlin` / `Swift`, the latest run showed `artifact_missing / artifact_size_mismatch / artifact_crc32_mismatch / run_failed` across multiple languages.

Observed results (2026-03-04):
- Kotlin (after gate removal):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304.json`
  - `cases=18 pass=2 fail=16`
  - `artifact_size_mismatch=4 (01..04)`, `artifact_missing=12 (05..16)`, `ok=2 (17,18)`
- Kotlin (after removing `save_gif` no-op):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304_after_gif.json`
  - `cases=18 pass=6 fail=12`
  - Confirmed `artifact_missing=0` (`artifact_size_mismatch=4 (01..04)`, `artifact_crc32_mismatch=8 (05,06,08,10,11,12,14,16)`)
- Kotlin (after aligning PNG writer with Python stored-block zlib spec):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_20260304_after_png_store.json`
  - `cases=18 pass=10 fail=8`
  - Confirmed `artifact_size_mismatch=0` (remaining issues are only `artifact_crc32_mismatch=8`)
- PyPy:
  - `work/logs/runtime_parity_sample_pypy_artifact_20260304.json`
  - `ok=16`, `no_artifact_python=2` (for artifact-generating cases, both size and CRC32 matched)
- Combined `cpp..kotlin` (before Swift was installed):
  - `work/logs/runtime_parity_sample_cpp_to_kotlin_crc_20260304.json`
  - Major failures:
    - `cpp`: `run_failed` (07,16) + `artifact_crc32_mismatch` (06,12,14)
    - `cs`: many `artifact_crc32_mismatch` in image cases
    - `js/ts`: `artifact_size_mismatch` for 01..04, `artifact_crc32_mismatch` in GIF cases
    - `go`: many `run_failed` (unresolved `any` typing, broken palette conversion, broken token type in `sample/18`)
    - `java`: many `artifact_missing` in image cases + `run_failed`
    - `kotlin`: `ok=18` at the time, but artifact verification was skipped then
- Swift:
  - Installed `Swift 6.2.4` with `swiftly`, enabling `swiftc`.
  - Re-ran with `--targets swift`; at least `sample/01..06` reproduced `run_failed` (function-call argument label mismatches).
- Swift (fixed full-run log with `--all-samples`):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets swift --cmd-timeout-sec 90 --summary-json work/logs/runtime_parity_sample_swift_crc_20260304_all_timeout90.json`
  - `cases=18 pass=0 fail=18`
  - Fixed categories as `run_failed=17`, `artifact_missing=1` (`sample/11`).
- Language baseline lock (reflecting Kotlin/Swift updates):
  - `work/logs/runtime_parity_sample_baseline_lock_20260304.json`
  - Fixed category breakdowns for `cpp/cs/go/java/js/kotlin/rs/swift/ts`.
- Java (after wiring runtime image calls):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets java --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_java_crc_20260304_after_image_connect.json`
  - `cases=18 pass=2 fail=16`
  - Confirmed `artifact_missing=0` (remaining: `artifact_size_mismatch=4`, `artifact_crc32_mismatch=7`, `run_failed=5`)
- Java (after fixing compile-fail group):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets java --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_java_crc_20260304_after_compile_fix4.json`
  - `cases=18 pass=6 fail=12`
  - Confirmed `run_failed=0` (remaining: `artifact_size_mismatch=4`, `artifact_crc32_mismatch=8`)
- Go (after `__pytra_bytes` + typed-operation return fixes):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets go --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_go_crc_20260304_after_s205b.json`
  - `cases=18 pass=16 fail=2`
  - `run_failed` shrank to only `sample/18` (`TokenLike` remaining). `palette must be 256*3 bytes` and `ifexp/min/max` compile failures were resolved.
- Go (after fixing broken `TokenLike` field access):
  - `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets go --cmd-timeout-sec 120 --summary-json work/logs/runtime_parity_sample_go_crc_20260304_after_s206.json`
  - `cases=18 pass=17 fail=1`
  - Confirmed `run_failed=0` (only remaining issue: `artifact_crc32_mismatch=1` for `sample/16`)

Root-cause findings (confirmed so far):
- Kotlin:
  - In `src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py`, `save_gif` falls back to `__pytra_noop`.
  - `src/runtime/kotlin/pytra/py_runtime.kt` has no GIF writer implementation.
  - PNG goes through `ImageIO`, so binaries do not match Python baseline (`01..04` size mismatch).
- Java:
  - `src/toolchain/emit/java/emitter/java_native_emitter.py` routes `save_gif/write_rgb_png` to `PyRuntime.__pytra_noop`.
  - Runtime side has `pyWriteRGBPNG/pySaveGif`, but artifacts are not generated because the emitter is not wired to them.
  - Additional `run_failed` from missing compatibility in `RuntimeError` references and `Map.get(key, default)`.
- Go:
  - `__pytra_bytes(v any)` does not handle `[]byte` and returns `[]any{}`, so palette via `grayscale_palette()` becomes empty and GIF fails with `palette must be 256*3 bytes`.
  - `__pytra_ifexp/__pytra_min/__pytra_max` return `any`; compile fails when type assertions are not inserted at typed assignment sites.
  - `sample/18` has broken type design preventing field access through `TokenLike`.
- Swift:
  - Emitter outputs function definitions as `f(x:y:...)`, while calls remain `f(a, b, ...)`, causing label mismatch compile errors.
- JS/TS:
  - PNG helper uses zlib deflate (level=6), so binary format does not match Python runtime (`01..04` size mismatch).
  - GIF also has many CRC mismatches; writer spec differences remain (LZW/chunk sequence/auxiliary values).
- C#:
  - Runtime side has PNG/GIF implementations, but CRC mismatches continue in image cases. Need to isolate whether this is writer-spec difference or input-side conversion difference.
- C++:
  - 07/16 are compile failures due to codegen regressions (`object` vs typed-list boundaries, undeclared variable).
  - 06/12/14 run but have CRC mismatches; numerical-path differences in image generation (optimization/type conversion/branching) are suspected.

Goal:
- Operate parity with Kotlin artifact skipping permanently removed.
- Formalize Swift parity logs after toolchain installation, and connect failures to repair planning.
- Fix failing toolchain/emit/runtimes and achieve size+CRC32 parity for artifact-generating cases in `sample`.

In scope:
- `tools/check/runtime_parity_check.py`
- `src/toolchain/emit/{kotlin,java,go,swift,js,ts,cs,cpp}/**`
- `src/runtime/{kotlin,java,go,js,ts,cs,cpp}/**`
- `tools/unittest/test_runtime_parity_check_cli.py`
- `docs/ja/todo/index.md` / this plan document

Out of scope:
- Execution-time optimization
- Updating benchmark tables in README
- New optimizations on Scala/Ruby/Lua/PHP side

Acceptance criteria:
- `runtime_parity_check --targets kotlin` runs with artifact verification enabled.
- On `runtime_parity_check --case-root sample --all-samples --targets cpp,rs,cs,js,ts,go,java,swift,kotlin`:
  - `artifact_missing=0`
  - `artifact_size_mismatch=0`
  - `artifact_crc32_mismatch=0`
  - `run_failed=0`
  - `toolchain_missing=0`
- The above is saved as `summary-json` logs, and reproduction steps are documented.

Verification commands (planned):
- `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets kotlin --summary-json work/logs/runtime_parity_sample_kotlin_crc_*.json`
- `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets swift --summary-json work/logs/runtime_parity_sample_swift_crc_*.json`
- `python3 tools/check/runtime_parity_check.py --case-root sample --all-samples --targets cpp,rs,cs,js,ts,go,java,swift,kotlin --summary-json work/logs/runtime_parity_sample_cpp_to_kotlin_crc_*.json`
- `python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

Decision log:
- 2026-03-04: Per user instruction, opened as P0 for Kotlin artifact-skip removal + Kotlin revalidation + fail-group root-cause analysis + rerun after Swift toolchain installation.
- 2026-03-04: Removed `ignore_artifacts=True` for Kotlin target from `tools/check/runtime_parity_check.py`.
- 2026-03-04: Installed `Swift 6.2.4` with `swiftly` and enabled `swiftc` (`/usr/local/bin/swiftc` symlink).
- 2026-03-04: Changed Kotlin emitter `save_gif/grayscale_palette` to runtime-helper wiring, and added GIF writer (`__pytra_save_gif`) to `src/runtime/kotlin/pytra/py_runtime.kt`. Resolved `artifact_missing`.
- 2026-03-04: Changed Kotlin `__pytra_write_rgb_png` to the same stored-block zlib/chunk construction as Python runtime, resolving size/CRC mismatches in 01..04.
- 2026-03-04: Added `--cmd-timeout-sec` to `tools/check/runtime_parity_check.py` so long-running Swift `sample/09` cannot stall the whole run. Regression confirmed on all 10 cases in `test_runtime_parity_check_cli.py`.
- 2026-03-04: Completed Swift `--all-samples` with timeout, and locked `run_failed=17/artifact_missing=1` as baseline.
- 2026-03-04: Merged Kotlin-updated and Swift-all logs into existing `cpp..kotlin` logs, generated `runtime_parity_sample_baseline_lock_20260304.json`, and fixed per-language categories.
- 2026-03-04: Wired Java emitter `write_rgb_png/save_gif/grayscale_palette` to `PyRuntime.pyWriteRGBPNG/pySaveGif/pyGrayscalePalette`, resolving `artifact_missing`.
- 2026-03-04: For Java compile-fail fixes, applied stringification for `RuntimeError` calls, typed fallback for `dict.get(key, default)`, direct `enumerate()` call handling, `__pytra_list_repeat` genericization, `Dict.entries` emit support, and `Raise` terminal detection. Reduced `run_failed` to 0.
- 2026-03-04: Added `__pytra_bytes([]byte)` conversion in Go runtime to resolve GIF palette empty-array issue (`palette must be 256*3 bytes`). Reinforced Go emitter so expressions from `ifexp/min/max` do not skip explicit casts even when inference matches, resolving typed-assignment compile failures.
- 2026-03-04: For Go `sample/18`, changed class typing to "classes with no subclasses are `*Class`", and added `dict.get(default)` runtime helper plus `Dict.entries` emit. Resolved broken `TokenLike` field access.
- 2026-03-04: Changed Swift emitter `_function_params` to `_ name: Type` format, resolving definition/call argument-label mismatch (`missing argument labels`). Confirmed `sample/01` parity `ok` (`work/logs/runtime_parity_sample_swift_case01_after_s207_20260304.json`) and disappearance of the same error in full-sample compile logs (`work/logs/swift_compile_all_after_s207_20260304.log`).
- 2026-03-04: Fixed JS emitter `Call` to merge keyword arguments (`kw_values/kw_nodes`) into positional arguments, resolving dropped `save_gif(delay_cs=..., loop=...)`. Replaced JS/TS PNG helpers with Python-equivalent stored-block zlib format; confirmed `ok` for all 18 cases on `--targets js,ts --all-samples` (`work/logs/runtime_parity_sample_js_ts_crc_20260304_after_s208.json`).
- 2026-03-04: Isolated C# mismatch causes: GIF side was missing keyword argument merge in `save_gif(delay_cs=..., loop=...)`; PNG side was rounding mismatch in `py_int` using `Convert.ToInt64` (incompatible with Python `int()`). Fixed keyword merge in C# emitter and changed `py_runtime.py_int` to `Math.Truncate` semantics; confirmed all 18 cases `ok` on `--targets cs --all-samples` (`work/logs/runtime_parity_sample_cs_crc_20260304_after_s209.json`).
- 2026-03-04: Fixed remaining C++ issues: wrong scope in `if/elif` pre-declaration, `object` regression in typed lists, self-init breakage in `for y in range(y, h)`, uninitialized `math.pi/e`, and missing unary `-` parentheses (`-(a+b)` -> `-a+b`). Revalidated `sample/06,07,12,14,16` and confirmed all `ok` (`work/logs/runtime_parity_sample_cpp_s210_focus_fixed_20260304.json`).
- 2026-03-04: Fixed missing `BitAnd/BitOr/BitXor/LShift/RShift` in Go emitter binary-operator mapping, where it had fallen back to default `+`. Confirmed `palette_332/quantize_332` in `sample/16` now uses correct bitwise operations; all 18 cases `ok` on `--targets go --all-samples` (`work/logs/runtime_parity_sample_go_after_bitop_fix_20260304.json`).
- 2026-03-04: In Kotlin emitter, merged `keywords` (`save_gif(delay_cs, loop)`) into positional args and fixed missing operator mappings for `BitAnd/BitOr/BitXor/LShift/RShift`. Normalized RHS of `shl/shr` to `.toInt()` to resolve compile failures; confirmed all 18 cases `ok` on `--targets kotlin --all-samples` (`work/logs/runtime_parity_sample_kotlin_after_shift_int_fix_20260304.json`).
- 2026-03-04: In Java emitter, merged `keywords`, fixed unary-minus parenthesis collapse (`-(a+b)` -> `-a+b`), and added mappings for `BitAnd/BitOr/BitXor/LShift/RShift`. Replaced Java runtime PNG writer from `Deflater` dependency to Python-equivalent stored-block zlib + Adler32 implementation; confirmed all 18 cases `ok` on `--targets java --all-samples` (`work/logs/runtime_parity_sample_java_after_png_unary_fix_20260304.json`).
- 2026-03-04: Revalidated `rs,cs,js,ts` on latest code and confirmed all 18 cases `ok` on `--targets rs,cs,js,ts --all-samples` (`work/logs/runtime_parity_sample_rs_cs_js_ts_after_s301_20260304.json`). Remaining items for `S3-01` were only full Swift completion and full `cpp` rerun.
- 2026-03-04: Updated `run_shell` in `tools/check/runtime_parity_check.py` to `start_new_session=True` + `os.killpg(SIGKILL)` so child processes (such as `*_swift.out`) are not orphaned on timeout. Also switched Swift execution to `swiftc -O`.
- 2026-03-04: As Swift revalidation, ran `01..04` and confirmed artifact parity 4/4 `ok` (`work/logs/runtime_parity_sample_swift_01_04_after_s301_progress_20260304.json`). Reconfirmed that with `--all-samples --cmd-timeout-sec 300`, `05/06/07` still timeout with `run_failed`, and organized the remaining issue as "execution strategy for heavy cases (timeout or Swift-side speedup)".
- 2026-03-04: As `S3-02`, added `swiftc -O` regression and timeout process-group kill regression to `test_runtime_parity_check_cli.py`. Documented mandatory artifact parity conditions (exists+size+CRC32), stale artifact purge, and timeout kill operational rules in `docs/ja/spec/spec-tools.md` / `docs/en/spec/spec-tools.md`.
- 2026-03-04: Added Subscript-assignment fast path to Swift emitter (direct index assignment on `Name` + `grid[y][x]` write-back), bypassing value-copy path of `__pytra_setIndex(Any, ...)`. Resolved timeouts/CRC failures in `05..09`; `--targets swift --all-samples --cmd-timeout-sec 300` progressed to `case_pass=11` (`work/logs/runtime_parity_sample_swift_all_after_subscript_store_opt_20260304.json`).
- 2026-03-04: Fixed Swift `_call_name` not resolving `Attribute`, which had dropped type inference for `math.sqrt/sin/...` to `Any`. Confirmed all 4 cases `10/14/15/16` as `ok` (`work/logs/runtime_parity_sample_swift_10_14_15_16_after_callname_attr_20260304.json`).
- 2026-03-04: Closed Swift `ForCore` in `do { ... }` scope to resolve loop-variable redeclaration conflicts, and changed tuple unpacking to declare `var` on first assignment. `12/13` became `ok`, and `--targets swift --all-samples --cmd-timeout-sec 300` progressed to `case_pass=17/case_fail=1` (remaining: compile fail in `18`) (`work/logs/runtime_parity_sample_swift_all_after_loop_scope_tuple_decl_20260304.json`).
- 2026-03-04: For remaining Swift `sample/18` issues, fixed entry recursion from inlined `main_guard`, `main -> __pytra_main` reference mismatch, missing `Dict.entries` literal support, and dict-subscript falling to runtime-helper value-copy path. `--targets swift 18_mini_language_interpreter` returned to `ok` (`work/logs/runtime_parity_sample_swift_18_after_dict_fix_20260304.json`).
- 2026-03-04: Re-ran `--targets swift --all-samples --cmd-timeout-sec 300` and confirmed all 18 cases `ok` (`work/logs/runtime_parity_sample_swift_all_after_s301_complete_20260304.json`). Remaining item for `S3-01` was only full `cpp` rerun.
- 2026-03-04: Re-ran `--targets cpp --all-samples --cmd-timeout-sec 300` and confirmed all 18 cases `ok` (`work/logs/runtime_parity_sample_cpp_all_after_s301_complete_20260304.json`). Together with existing all-`ok` logs for `rs/cs/js/ts/go/java/swift/kotlin`, this satisfies `S3-01` acceptance criteria (`mismatch/run_failed/toolchain_missing=0`).

## Breakdown

- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-01] Fix baseline (summary-json) after removing Kotlin artifact gate, and lock failure categories per language.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S1-02] Complete `--targets swift --all-samples` after Swift toolchain installation and lock failure categories.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-01] Kotlin: remove `save_gif` no-op path, implement runtime GIF writer, and resolve `artifact_missing` for 05..16.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-02] Kotlin: align PNG writer to Python-compatible binary format and resolve artifact size/CRC mismatches for 01..04.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-03] Java: wire image calls in emitter from `__pytra_noop` to runtime implementation and resolve `artifact_missing`.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-04] Java: fix compile failures around `RuntimeError` / dict.get-default / typing and enable complete sample execution.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-05] Go: fix `__pytra_bytes([]byte)` and typed-operation return type resolution (`ifexp/min/max`) to resolve `run_failed`.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-06] Go: fix broken `TokenLike` field access in `sample/18` and resolve parser/tokenize compile failures.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-07] Swift: fix argument-label alignment between function definitions and calls, and make all samples compile/run.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-08] JS/TS: align PNG/GIF helpers to Python-compatible binary writer and resolve size/CRC mismatches.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-09] C#: isolate cause of image CRC mismatches (writer spec difference or input conversion difference) and align to Python-compatible binary.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S2-10] C++: fix sample/07,16 compile failures, then remove causes of CRC mismatches in 06/12/14 and align outputs.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-01] Re-run artifact parity on all `cpp,rs,cs,js,ts,go,java,swift,kotlin`, and verify `mismatch/run_failed/toolchain_missing=0`.
- [x] [ID: P0-MULTILANG-ARTIFACT-CRC-ALIGN-01-S3-02] Reflect artifact parity operation (CRC32 required) in regression tests and `docs/ja/spec`.
