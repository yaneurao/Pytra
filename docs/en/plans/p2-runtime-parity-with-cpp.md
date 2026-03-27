<a href="../../ja/plans/p2-runtime-parity-with-cpp.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Bring multi-language runtimes to C++ parity, redesigned with strict SoT and generation-first rules

Last updated: 2026-03-05

Related TODO:
- `ID: P2-RUNTIME-PARITY-CPP-02` in `docs/ja/todo/index.md`

Background:
- The old P2, `P2-RUNTIME-PARITY-CPP-01`, rushed parity and left the boundary between runtime implementation and generated implementation ambiguous, which let policy mistakes creep in.
- Concretely, areas that should have prioritized machine generation from the pure Python source of truth were still vulnerable to handwritten per-language implementations, special naming, and monolithic embedding.
- Some emitter paths also still branched directly on library function names by string comparison, repeating a violation of the intended IR-side resolution responsibility.

Goal:
- Keep API-contract parity with the C++ runtime while redefining implementation policy around three principles: strict source of truth, generation-first, and separated responsibilities.
- Fix runtime parity in a way that cannot regress, using design rules, static guards, and parity regressions.

Scope:
- `src/runtime/<lang>/{pytra-core,pytra-gen}/`
- `src/pytra/{std,utils}/`, source-of-truth modules
- `src/toolchain/emit/*/emitter/*.py`, runtime-call paths
- `tools/`, audit, generation, parity, and CI paths

Out of scope:
- Large redesign of the C++ runtime itself
- Full EAST-spec rewrite
- All-language migration in a single wave

## Mandatory notes

The following are mandatory rules, not recommendations.

1. Treat the pure Python implementations under `src/pytra/std/*` and `src/pytra/utils/*` as the source of truth and do not hand-reimplement corresponding functionality in other languages.
2. Always place SoT-derived code under `src/runtime/<lang>/pytra-gen/` and never mix it into `pytra-core`.
3. Use straight-through mechanical naming for SoT-derived files, for example `png.py -> png.<ext>` and `gif.py -> gif.<ext>`, and forbid special helper naming.
4. Keep only language-dependent foundational processing in `pytra-core`. Any API that can be expressed from the SoT belongs in `pytra-gen`.
5. Forbid emitter branches that hard-code `pytra.std.*` or `pytra.utils.*` function names through checks such as `callee_name == "..."` or `attr_name == "..."`.
6. Put responsibility for resolving runtime and stdlib calls on the lower/IR side. Emitters must only render already-resolved nodes such as `runtime_call`.
7. Do not depend on Python's standard `ast` module in compiler or backend code, because of selfhost constraints.
8. Require `source:` and `generated-by:` markers in every `pytra-gen` artifact, and fail fast in audits when they are missing.
9. Always clean artifacts before parity runs, and validate artifact size and CRC32 in addition to stdout.

## Acceptance criteria

- The old P2, `P2-RUNTIME-PARITY-CPP-01`, is removed from the unfinished TODO list and replaced with the new ID.
- The prohibitions required to execute the new P2 are documented and managed in a checkable form, script or CI.
- Audits for naming, placement, and markers in `pytra-gen` pass across all target languages.
- Direct hard-coded runtime branches in non-C++ emitters are removed in stages.
- Runtime-originated failures become traceable through parity regressions, including artifact size and CRC32.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`

## Breakdown

- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] Remove the old P2, `P2-RUNTIME-PARITY-CPP-01`, from the unfinished TODO list and replace it with the new P2.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] Add SoT, `pytra-core`, and `pytra-gen` responsibility boundaries to `docs/ja/spec` and fix the prohibitions in writing.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] Create a classification table for target modules under `std/utils`, generated required or core allowed.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] Add a static check that detects naming-rule violations in `pytra-gen`, using straight-through naming as the standard.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] Strengthen checks for SoT markers, `source/generated-by`, and placement violations, mixing generated code into `pytra-core`, and integrate them into CI.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] Inventory traces of SoT reimplementation inside `pytra-core` and reflect them into the migration plan for `pytra-gen`.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Use Java as the first target and unify runtime API calls onto the IR-resolved path, removing direct emitter branches.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Extend the same policy to all other non-C++ backends, `cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] Turn the emitter prohibition rules, hard-coded library names, into lint rules and make PR and CI fail fast.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] Re-run sample parity, including artifact size and CRC32, across all target languages and fix the resulting baseline.
- [x] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] Reflect local and CI operating procedure into `docs/ja/how-to-use` and `docs/en/how-to-use` so rule violations are caught immediately when they recur.

## S2-03 Inventory Results (2026-03-05)

Raw log: `work/logs/runtime_core_sot_reimpl_inventory_20260305_s2_03.tsv`

| Language | Reimplementation-trace file in `pytra-core` | Trace category | Migration policy |
| --- | --- | --- | --- |
| `cs` | `src/runtime/cs/pytra-core/std/json.cs` | JSON implementation body | Move to generated `pytra-gen/std/json.cs` from the source-of-truth `src/pytra/std/json.py`, and allow only a thin adapter in core. |
| `go` | `src/runtime/go/pytra-core/built_in/py_runtime.go` | JSON plus image-helper stubs | Move JSON to `pytra-gen/std/json.go`; reduce image helpers to delegation into `pytra-gen/utils/{png,gif}.go`. |
| `kotlin` | `src/runtime/kotlin/pytra-core/built_in/py_runtime.kt` | JSON implementation body | Introduce `pytra-gen/std/json.kt` and remove the core-side JSON implementation. |
| `lua` | `src/runtime/lua/pytra-core/built_in/py_runtime.lua` | JSON implementation body | Move to generated `pytra-gen/std/json.lua` and remove JSON encode and decode from core. |
| `php` | `src/runtime/php/pytra-core/py_runtime.php` | JSON implementation plus legacy include | Move to generated `pytra-gen/std/json.php`; keep only delegation in `py_runtime.php`. |
| `ruby` | `src/runtime/ruby/pytra-core/built_in/py_runtime.rb` | JSON wrapper | Introduce `pytra-gen/std/json.rb` and reduce the core API to a forwarder. |
| `scala` | `src/runtime/scala/pytra-core/built_in/py_runtime.scala` | JSON implementation body | Generate `pytra-gen/std/json.scala` and remove the core implementation. |
| `swift` | `src/runtime/swift/pytra-core/built_in/py_runtime.swift` | JSON implementation body | Generate `pytra-gen/std/json.swift` and reduce core to an adapter. |
| `rs` | `src/runtime/rs/pytra-core/built_in/py_runtime.rs` | Mixed image markers plus image export | Unify image markers and re-exports on the `pytra-gen/utils` side and remove marker mixing in core, currently a single allowlist shrink target. |
| `cpp` | `src/runtime/cpp/pytra-core/built_in/py_runtime.h`, `re.sub` comment | False positive, no implementation trace | Out of inventory scope. Confirmed to be only a regex-related comment and not an SoT reimplementation. |

Migration waves:

1. Wave A, JSON: move the JSON implementations for `cs/go/kotlin/lua/php/ruby/scala/swift` into `pytra-gen/std/json.<ext>`.
2. Wave B, image runtime: reduce the core-side image traces in `rs/go` into delegation to `pytra-gen/utils/{png,gif}` and eliminate mixed markers.
3. Wave C, audit convergence: shrink the allowlists, `runtime_core_gen_markers` and `runtime_pytra_gen_naming`, in stages and fix the diff in `S4-01` parity.

Decision log:
- 2026-03-05: On user instruction, discarded the old P2 and replaced it with this redesigned version based on strict SoT, generation-first policy, and separated responsibilities.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-01`] Replaced the old unfinished P2 residue, `docs/en/todo/index.md` and `docs/en/plans/p2-runtime-parity-with-cpp.md`, with the new P2 structure and removed unfinished-list references to the old ID.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-02`] Added a new section on the SoT, `pytra-core`, and `pytra-gen` responsibility boundary to `docs/ja/spec/spec-runtime.md`. Documented shared mandatory rules across all languages, generation-first, mandatory markers, and rendering only already-resolved EAST3 nodes, as well as prohibitions, no core reimplementation, no special naming, and no direct emitter string branches. Fixed the audit commands at the same time.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S1-03`] Added a `std/utils` classification table to `docs/ja/spec/spec-runtime.md`, marking `argparse..typing` and `assertions/gif/png` as generated-required, while `dataclasses_impl/math_impl/time_impl` are explicitly allowed in `pytra-core` as implementation-boundary exceptions.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-01`] Added `tools/check_runtime_pytra_gen_naming.py`, enabling static detection of naming and placement violations under `pytra-gen` for `std|utils` straight-through naming. Existing debt is explicitly tracked in `tools/runtime_pytra_gen_naming_allowlist.txt`, 11 items, and both `test/unit/tooling/test_check_runtime_pytra_gen_naming.py` and the main check passed.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-02`] Added `tools/check_runtime_core_gen_markers.py`, making marker requirements, `source/generated-by`, under `pytra-gen` and forbidding generated-marker mixing into `pytra-core`, a static audit across all languages. Integrated both `check_runtime_core_gen_markers.py` and `check_runtime_pytra_gen_naming.py` into `tools/run_local_ci.py`, and confirmed passing for `test_check_runtime_core_gen_markers.py`, `test_check_runtime_pytra_gen_naming.py`, and both main checks.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S2-03`] Inventoried SoT reimplementation traces in `pytra-core`, 10 files, in `work/logs/runtime_core_sot_reimpl_inventory_20260305_s2_03.tsv`. Classified them into JSON, 8 languages, and image runtime, `rs/go`, and reflected migration waves A, B, and C into the plan.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-01`] Re-audited Java as the lead migration target by running `check_emitter_runtimecall_guardrails.py`, strict backend `java`, and `test_py2java_smoke.py`, 25 cases, confirming no reintroduction of hard-coded runtime branches. Since the `_render_resolved_runtime_call` path and `resolved_runtime_call` contract remain intact, `S3-01` is marked complete.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-02`] Re-verified the non-Java rollout by re-running `check_emitter_runtimecall_guardrails.py`, no findings on all backends, and `test_py2{rs,rb,lua,scala,swift,ts}_smoke.py`, 127 cases. Together with already-run smoke for `go/php/kotlin/js/nim/cs`, 117 cases, this confirmed non-regression of the IR-resolved path and fail-closed policy across all 12 target backends.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S3-03`] Reconfirmed that `check_emitter_runtimecall_guardrails.py` and `check_emitter_forbidden_runtime_symbols.py` run as mandatory steps in `tools/run_local_ci.py`. Because strict backend mode, `java`, fails immediately without relying on an allowlist, the PR and CI prohibition rule is now fixed in fail-fast form.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Started re-running sample parity and fixed all 14-target results for `01_mandelbrot` and `02_raytrace_spheres` in `work/logs/runtime_parity_sample01_multilang_20260305.json` and `work/logs/runtime_parity_sample02_multilang_20260305.json`. Main failure categories were `js/ts`, PNG runtime export mismatch, `go`, generated PNG and GIF compile errors plus `main` collisions, `nim`, invalid module name starting with a digit, `cpp(02)`, duplicate `main` links plus unresolved `write_rgb_png`, and `java(02)`, mismatch between `math.java` class and filename.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Fixed Nim `run_failed`, invalid module name, by forcing Nim output names to `main.nim` in `pytra_cli_profiles.py` and adding stderr fallback plus warning filtering in `runtime_parity_check.py`. Nim parity for `01_mandelbrot` and `02_raytrace_spheres` then passed with matching artifact size and CRC32 in `work/logs/runtime_parity_sample0{1,2}_nim_after_stderr_fallback_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Re-ran `runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim --all-samples --ignore-unstable-stdout` and confirmed `js/ts/go/nim` failures on `01`, plus `java/cpp` failures on `02/03`. Main causes were an f-string left in `js/png.js`, broken string emission in `go/png.go`, Nim executable module-name restrictions, Java runtime class naming drift, temporary `tmp`, and duplicate `main` plus unresolved `write_rgb_png` on the C++ runtime side. `rs/cs/ruby/lua/php/swift/kotlin/scala` were confirmed to match artifact size and CRC32 at least for samples `01-03`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Normalized the SoT implementation in `src/pytra/utils/png.py` toward backend compatibility, removing f-strings and replacing `bytes([..])`, then regenerated with `gen_runtime_from_manifest.py --items utils/png --targets js,ts,go`. Re-verifying `01_mandelbrot` advanced `js/ts` from syntax errors to unresolved `write_rgb_png` export, and fixed the string-emission breakage in `go`, though `extend/main` duplication and undefined `pyWriteRGBPNG` still remained.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Added pre-cleanup of target-specific output directories in `runtime_parity_check.py`, removing stale transpile and build artifacts before each run. Re-ran `runtime_parity_check.py --case-root sample --targets js,ts,go,cpp,java,nim 01_mandelbrot 02_raytrace_spheres` and confirmed artifact size and CRC32 match on all six targets in `work/logs/runtime_parity_sample01_02_focus_20260305_after_freshfix.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Restored the non-C++ runtimes, temporarily moved aside during the C++ lead migration, from `src/runtime2/{rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim}` back into `src/runtime/`, resolving the chain of `runtime source not found` failures in backend-registry runtime hooks.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Because PHP still mismatched on `write_rgb_png/save_gif`, fixed `resolved_runtime_call` behavior in `php_native_emitter`, raw-name use only for a single symbol, added by-reference handling for `_*_append_list(&$dst, ...)` in the PHP postprocess inside `gen_runtime_from_manifest.py`, and strengthened `open`, `PyFile`, and bytes conversion in `runtime/php/pytra-core/py_runtime.php`. Then confirmed 14-target parity, artifact size and CRC32, for `sample/01` and `sample/02` in `work/logs/runtime_parity_sample01_02_all_targets_after_php_runtime_fixes_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Fixed Nim residual differences, `save_gif` returning `int`, causing a statement-without-discard error, and `math.pi`, still lacking normalization to `PI`. Updated `nim_native_emitter.py` and `runtime/nim/{pytra,pytra-gen}/utils`, then confirmed 14-target parity, artifact size and CRC32, on samples `04`, `05`, and `06` in `work/logs/runtime_parity_sample04_06_all_targets_after_nim_fix_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Found Lua artifact mismatches on `07-09` and fixed `IfExp` in `lua_native_emitter.py` to use `__pytra_truthy`-based lazy evaluation. Re-running confirmed 14-target artifact size and CRC32 match for `07/08/09` in `work/logs/runtime_parity_sample07_09_all_targets_after_lua_scope_fix_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Fixed remaining failures on `10-12`, `nim: math.sqrt(int)` and `lua: max/min resolution collision`, by adding a float cast for `sqrt` in the Nim emitter and `_G.math.max/min` in the Lua emitter. Confirmed 14-target artifact size and CRC32 match for `10/11/12` in `work/logs/runtime_parity_sample10_12_all_targets_after_lua_nim_fix_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Fixed `php: stdlib.method.pop` unresolved in `13-15` and restored the fallback path. Confirmed 14-target artifact size and CRC32 match for `13/14/15` in `work/logs/runtime_parity_sample13_15_all_targets_after_php_pop_fix_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] Fixed the remaining failures in `16-18`, Ruby, Scala, and Lua bit-operator symbol maps, Scala injection of `runtime_owner` into `stdlib.method.*`, and Lua localization of first assignments in functions plus declaration-only tracking. Confirmed 14-target artifact size and CRC32 match for `16/17/18` in `work/logs/runtime_parity_sample16_18_all_targets_after_fixes_20260305.json`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-01`] As regression confirmation after those changes, re-ran `01-03` and `04-06` across all 14 targets and confirmed artifact size and CRC32 match in `work/logs/runtime_parity_sample01_03_all_targets_after_lua_decl_fix_20260305.json` and `work/logs/runtime_parity_sample04_06_all_targets_after_lua_decl_fix_20260305.json`. This fixed the sample baseline at `pass=18, fail=0`.
- 2026-03-05: [ID: `P2-RUNTIME-PARITY-CPP-02-S4-02`] Added a parity runbook section to `docs/ja/how-to-use.md` and `docs/en/how-to-use.md`, documenting the 14-target command, artifact size and CRC32 comparison, automatic stale-artifact cleanup, and recommended case grouping.
