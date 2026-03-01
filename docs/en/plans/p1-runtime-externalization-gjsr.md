# P1: Runtime Externalization for Go/Java/Swift/Ruby (Remove Inline Helpers)

Last updated: 2026-02-28

Related TODO:
- `ID: P1-RUNTIME-EXT-01` in `docs/ja/todo/index.md`

Background:
- Generated code in `sample/go`, `sample/java`, `sample/swift`, and `sample/ruby` inlines runtime helper bodies such as `__pytra_truthy` at file top.
- Inline expansion has the benefit that a single generated file can run as-is, but it causes generated-code bloat, duplicated runtime implementations, and harder runtime replacement.
- Go/Java already have runtime bodies under `src/runtime/<lang>/pytra`, but current native emitter and runtime execution paths are not connected.
- In Swift, `src/runtime/swift/pytra/py_runtime.swift` still contains sidecar-era Node helper implementation, and native runtime API source of truth is not yet prepared.
- Ruby started with a design embedding runtime helpers in generated artifacts and does not yet have an external runtime file.

Objective:
- Remove inline helper definitions from native generated code for Go/Java/Swift/Ruby, and unify on separate runtime file references.
- Consolidate runtime source of truth under `src/runtime/<lang>/pytra/`, with generated code limited to API calls.

Scope:
- `src/hooks/go/emitter/go_native_emitter.py`
- `src/hooks/java/emitter/java_native_emitter.py`
- `src/hooks/swift/emitter/swift_native_emitter.py`
- `src/hooks/ruby/emitter/ruby_native_emitter.py`
- `src/runtime/go/pytra/*`, `src/runtime/java/pytra/*`, `src/runtime/swift/pytra/*`, `src/runtime/ruby/pytra/*`
- `tools/runtime_parity_check.py`, `tools/regenerate_samples.py`, `test/unit/test_py2{go,java,swift,rb}_smoke.py`

Out of scope:
- Runtime model changes for C++/Rust/C#/JS/TS backends
- Full redesign of runtime API semantics itself
- Full selfhost completion across all languages (separate task)

Acceptance Criteria:
- `py2go` / `py2java` / `py2swift` / `py2rb` generated code does not inline helper bodies such as `__pytra_truthy`.
- Build/run path in each language works by external runtime references (import/link/include).
- Existing pass range in `runtime_parity_check` is verified as non-regressive.
- Regeneration of `sample/{go,java,swift,ruby}` does not break runtime execution paths.

Validation Commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,java,swift,ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs go,java,swift,ruby --force`

Decision Log:
- 2026-02-27: Per user request, filed policy as `P1-RUNTIME-EXT-01` to avoid embedding inline runtime helpers in Go/Java/Swift/Ruby.
- 2026-02-28: As `S1-01`, created inventory of inline helpers and runtime source-of-truth API mappings; fixed that Go/Java mainly require naming-gap adaptation, while Swift/Ruby mainly lack runtime source-of-truth implementations.
- 2026-02-28: As `S2-01`, removed inline `func __pytra_*` definitions from Go emitter, consolidated compatible helpers in `src/runtime/go/pytra/py_runtime.go`, switched `py2go.py` to place `py_runtime.go` at output target, and confirmed non-regression with `test_py2go_smoke.py` and `runtime_parity_check --targets go` (`sample/18`).
- 2026-02-28: As `S2-02`, removed helper body definitions from Java emitter and migrated calls to `PyRuntime.__pytra_*`. Consolidated compatible helpers in `src/runtime/java/pytra/built_in/PyRuntime.java`, switched `py2java.py` to place `PyRuntime.java` at output target, and confirmed non-regression with `test_py2java_smoke.py` and `runtime_parity_check --targets java` (`sample/18`).
- 2026-02-28: As `S2-03`, stopped helper inline emission in Swift emitter and consolidated helper set in `src/runtime/swift/pytra/py_runtime.swift`. Switched `py2swift.py` to place `py_runtime.swift` at output target and passed `test_py2swift_smoke.py`. For `runtime_parity_check --targets swift`, confirmed `toolchain_missing` due to no `swiftc` in environment.
- 2026-02-28: As `S2-04`, removed inline helper bodies from Ruby emitter and switched generated code to `require_relative "py_runtime"` references. Added `src/runtime/ruby/pytra/py_runtime.rb` and added path in `py2rb.py` to place `py_runtime.rb` at output target. Confirmed non-regression with `test_py2rb_smoke.py` and `runtime_parity_check --targets ruby` (`sample/18`).
- 2026-02-28: As `S3-01`, re-ran `test_py2{go,java,swift,rb}_smoke.py` and confirmed all pass. On `runtime_parity_check --case-root sample --targets go,java,swift,ruby --all-samples --ignore-unstable-stdout`, confirmed `cases=18 pass=18 fail=0` (`swift` is `toolchain_missing`). Added `ruby` to `tools/regenerate_samples.py`, ran `--langs go,java,swift,ruby --force` (`total=72 regen=72 fail=0`), and locked sample-regeneration path.

## S1-01 Inventory Results (2026-02-28)

| Language | Inline helper output location | Inline helper scale | Runtime source of truth | Notes |
| --- | --- | --- | --- | --- |
| Go | In `transpile_to_go_native` of `src/hooks/go/emitter/go_native_emitter.py` (directly writes `func __pytra_*`) | `32` definitions (`__pytra_truthy/int/float/str/len/get_index/set_index/slice/print/perf_counter`, etc.) | `src/runtime/go/pytra/py_runtime.go` (`pyBool/pyToInt/pyToFloat/pyToString/pyLen/pyGet/pySet/pySlice/pyPrint/pyPerfCounter`, etc.) | Semantic coverage is aligned but names/signatures mismatch. Externalization is possible by switching emitter-side call names and adding import path. |
| Java | In `transpile_to_java_native` of `src/hooks/java/emitter/java_native_emitter.py` (`private static __pytra_*`) | `10` definitions (`__pytra_noop/int/len/str_isdigit/str_isalpha/str_slice/bytearray/dict_of/list_repeat/truthy`) | `src/runtime/java/pytra/built_in/PyRuntime.java` (`pyToLong/pyLen/pyIsDigit/pyIsAlpha/pySlice/pyBytearray/pyDict/pyList/pyBool`, etc.) | Runtime source is rich. Need a glue layer that consolidates inline `__pytra_*` calls to `PyRuntime.py*`. |
| Swift | `_emit_runtime_helpers()` in `src/hooks/swift/emitter/swift_native_emitter.py` | `32` definitions (`__pytra_any_default/int/float/str/len/getIndex/setIndex/slice/print/perf_counter`, etc.) | `src/runtime/swift/pytra/py_runtime.swift` (only `pytraRunEmbeddedNode`) | Native runtime API source-of-truth is not prepared. Must add Swift-side `py*` API group in runtime before externalization. |
| Ruby | `src/hooks/ruby/emitter/ruby_native_emitter.py` (helper references only) | `26` definitions (`__pytra_truthy/int/float/div/str/len/as_list/as_dict/get_index/set_index/slice/print/perf_counter`, etc.) | `src/runtime/ruby/pytra/py_runtime.rb` | Standardize emitter side to `require_relative "py_runtime"`, and place runtime in same output directory via `py2rb.py`. |

### Mapping Table (minimum required APIs)

| Inline helper semantics | Go runtime source API | Java runtime source API | Swift runtime source | Ruby runtime source |
| --- | --- | --- | --- | --- |
| truthy check | `pyBool` | `pyBool` | `TBD (new)` | `__pytra_truthy` |
| int conversion | `pyToInt` / `pyToLong` | `pyToLong` | `TBD (new)` | `__pytra_int` |
| float conversion | `pyToFloat` | `pyToFloat` | `TBD (new)` | `__pytra_float` |
| stringify | `pyToString` | `pyToString` | `TBD (new)` | `__pytra_str` |
| length | `pyLen` | `pyLen` | `TBD (new)` | `__pytra_len` |
| index read/write | `pyGet` / `pySet` | `pyGet` / `pySet` | `TBD (new)` | `__pytra_get_index` / `__pytra_set_index` |
| slice | `pySlice` | `pySlice` | `TBD (new)` | `__pytra_slice` |
| print | `pyPrint` | `pyPrint` | `TBD (new)` | `__pytra_print` |
| perf_counter | `pyPerfCounter` | `pyPerfCounter` | `TBD (new)` | `__pytra_perf_counter` |

## Breakdown

- [x] [ID: P1-RUNTIME-EXT-01-S1-01] Create language-by-language helper output inventory (inline) and runtime source API mapping table.
- [x] [ID: P1-RUNTIME-EXT-01-S2-01] Remove helper-body output from Go emitter and switch to `src/runtime/go/pytra` API calls.
- [x] [ID: P1-RUNTIME-EXT-01-S2-02] Remove helper-body output from Java emitter and switch to `src/runtime/java/pytra` API calls.
- [x] [ID: P1-RUNTIME-EXT-01-S2-03] Prepare native runtime implementation for Swift and remove emitter helper inline output.
- [x] [ID: P1-RUNTIME-EXT-01-S2-04] Add Ruby runtime implementation and switch to external-reference mode via `require_relative` etc.
- [x] [ID: P1-RUNTIME-EXT-01-S3-01] Update parity/smoke/sample-regeneration paths and complete regression verification.
