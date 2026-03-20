# P3: Roll Out Container Reference-Management Model to non-C++ Backends

Last updated: 2026-03-02

Related TODO:
- `ID: P3-MULTILANG-CONTAINER-REF-01` in `docs/ja/todo/index.md`

Background:
- In the C++ backend, `cpp_list_model=pyobj` adopts a policy that reference-manages containers at `object` boundaries while reducing typed and non-escape paths to value types.
- In non-C++ backends, memory models and container implementations are split per language, and the equivalent policy ("dynamic boundaries use reference management, typed known non-escape paths use value types") has not been handled explicitly.
- This difference causes variance in output quality, optimization behavior, and maintainability, reducing design consistency across toolchain.emit.

Objective:
- Roll out the same abstract policy used in C++ to non-C++ backends (`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua`).
- The policy is not "port RC implementation everywhere," but "unify reference-management boundary spec + common typed/non-escape value-reduction rules."

Scope:
- Spec/IR layer: `src/pytra/compiler/east_parts/*` (propagation of container ownership-form metadata)
- Backends: `src/hooks/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua}/emitter/*`
- Runtime support: `src/runtime/{rs,cs,go,java,kotlin,swift,ruby,lua}/**` (only where needed)
- Validation:
  - `test/unit/test_*emitter*.py`
  - `tools/runtime_parity_check.py` (with target backend selection)
  - Regenerated diffs in `sample/*`

Out of scope:
- Additional redesign for C++ backend (full revamp of existing `cpp_list_model`)
- New PHP backend addition
- Whole selfhost-completion task (this plan is limited to container reference-management policy)

Acceptance Criteria:
- A common spec for non-C++ backends around "reference-management boundary / value reduction" is documented, and IR metadata contract is defined.
- Pilot implementation is complete in at least `rs` + one GC backend, and locked by regression tests.
- Rollout steps and blockers for remaining backends are trackable as TODO child tasks.
- Major sample/parity cases confirm non-regressive behavior.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_*emitter*.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py --case-root sample --targets rs,cs,go,java,kotlin,swift,ruby,lua`
- `python3 tools/check_todo_priority.py`

## S1-01 Current Model Audit (Gap Matrix)

| backend | language memory model | typed-known container path | dynamic-boundary path | current gap |
|---|---|---|---|---|
| `rs` | ownership/borrow (no GC) | `Vec<T>` / `BTreeMap<K,V>` (partial `HashMap`) | `PyAny::List/Dict/Set` | Uses backend-local heuristics without ownership-hint references. |
| `cs` | GC | `List<T>` / `Dictionary<K,V>` | `object` + cast helpers | Contract for non-escape judgment and value/ref split is not unified. |
| `go` | GC | known types + some struct paths | `any`, `[]any`, `map[any]any` | `any` fallback conditions are under-specified. |
| `java` | GC | primitive + known classes | `Object`, `ArrayList<Object>`, `HashMap<Object,Object>` | Dynamic-boundary judgment is emitter-local. |
| `kotlin` | GC (JVM) | `MutableList<T>` / `MutableMap<K,V>` (when typed-known) | `Any?`, `MutableList<Any?>` | Downgrade conditions to `Any?` are backend-specific. |
| `swift` | ARC | Swift value/reference types | `Any`, `[Any]`, `[AnyHashable: Any]` | ARC-oriented boundary handling is not connected to IR contracts. |
| `js` | GC | effectively dynamic (Array/Object) | via `py_runtime` helpers | typed/non-escape concept is not operated. |
| `ts` | GC | currently reused `js` emitter (JS-compatible) | same as `js` | TS-specific type-boundary rules are not prepared. |
| `ruby` | GC | effectively dynamic (Array/Hash) | via runtime helpers | value-path reduction metadata is unused. |
| `lua` | GC | effectively dynamic (table) | via `__pytra_*` helpers | escape-condition integration has not started. |

## S1-02 Common Terms and Judgment Rules (v1)

- `container_ref_boundary`:
  - A point that flows into `object/Any/unknown/union(with any)` or is passed to unknown calls.
  - At this boundary, lower to backend-specific reference-management representations (boxed/Any/GC reference).
- `typed_non_escape_value_path`:
  - A local path where element types are concrete and `escape_condition` is not satisfied.
  - Prioritize backend value-oriented containers (`Vec<T>`, `List<T>`, `MutableList<T>`, etc.).
- `escape_condition` (fail-closed):
  - Returned outward as a function result.
  - Assigned to `object/Any`.
  - Passed as an argument to unknown/external calls.
  - Lifetime/ownership escapes local scope through field save or aliasing.
  - If judgment is impossible, treat as escape.
- `backend_adaptation_rule`:
  - Common IR supplies boundary-judgment metadata; concrete memory-management strategy (GC/ARC/borrow) is backend responsibility.
  - The goal is not RC porting, but lowering each language into its natural reference representation under one shared boundary judgment.

## S2-01 EAST3 Ownership-Hint Minimal Extension Design (v1)

- Added metadata:
  - `module.meta.container_ownership_hints_v1` (dict)
  - key: stable symbol name (`<scope>::<name>`)
  - value:
    - `container_type`: e.g. `list[Token]`, `dict[str, int64]`
    - `element_type`: e.g. `Token`, `int64`
    - `boundary_mode`: `"value_path" | "ref_boundary"`
    - `escape`: `true | false`
    - `reason_codes`: e.g. `["unknown_call_escape", "any_flow"]`
    - `source_pass`: e.g. `"non_escape_interprocedural_pass"`
- Node references:
  - Store keys on `meta.container_ownership_hint_ref` for `AnnAssign` / `Assign` / `FunctionDef(args, return)`, and resolve from emit side.
- Propagation rules:
  - Alias (`b = a`) inherits the key, but if any escape condition is satisfied, immediately promote to `boundary_mode=ref_boundary`.
  - For call arguments, if callee summary is unknown, set `escape=true` fail-closed.
  - Containers carried on return paths are `escape=true` by default (except explicit non-escape cases).
- Fail-closed contract:
  - Unresolved keys, type mismatch, and unknown `reason_codes` all fall back to `ref_boundary`.

## S2-02 CodeEmitter Base API Design (backend-neutral)

- Minimal API additions to `CodeEmitter` (proposal):
  - `resolve_container_ownership_hint(symbol: str, east_type: str) -> dict[str, Any]`
  - `classify_container_boundary(hint: dict[str, Any], east_type: str) -> str`
  - `should_emit_typed_value_container(hint: dict[str, Any], east_type: str, backend_caps: dict[str, bool]) -> bool`
- Backend capability flags (examples):
  - `supports_typed_container_value_path`
  - `supports_dynamic_ref_boundary`
  - `supports_zero_copy_container_iter`
- Base responsibilities:
  - Hint resolution, fail-closed judgment, and boundary classification (`value_path` or `ref_boundary`).
- Backend responsibilities:
  - Map classification results to language-specific representations (`Vec<T>` / `List<T>` / `Any` / table, etc.).
  - Keep existing runtime-helper connection logic (boxing/unboxing/cast).

## S3-01 Rust Pilot Implementation Notes

- Changes:
  - Added "reference-argument -> value-local" reduction in `rs_emitter._render_value_for_decl_type`.
  - When initializing value-typed locals from reference values in `current_ref_vars` via `AnnAssign`:
    - `list[...]` / `bytes` / `bytearray`: `to_vec()`
    - `dict[...]` / `set[...]` / `tuple[...]` / class types: `clone()`
- Intent:
  - Prevent breakage where `&[T]` / `&BTreeMap<...>` would be assigned directly to value variables on `typed_non_escape_value_path`, and materialize values in line with Rust ownership rules.
- Regression lock:
  - `test_py2rs_smoke.py::test_ref_container_args_materialize_value_path_with_to_vec_or_clone`
  - `tools/check_py2rs_transpile.py`
  - `tools/runtime_parity_check.py --case-root sample --targets rs --ignore-unstable-stdout 18_mini_language_interpreter`

## S3-02 Kotlin Pilot Implementation Notes (GC backend)

- Changes:
  - Added `ref_vars` context in `kotlin_native_emitter`, and track container-type function arguments (`list/tuple/dict/set/bytes/bytearray`) as `container_ref_boundary`.
  - In `AnnAssign/Assign` declaration/re-assignment, when RHS starts from `ref_vars` and LHS is a container type:
    - `MutableList<...>`: `__pytra_as_list(src).toMutableList()`
    - `MutableMap<...>`: `__pytra_as_dict(src).toMutableMap()`
    are inserted, fixing typed/non-escape paths to "materialize a separate instance".
  - Kept fail-closed fallback to current paths when judgment is impossible (not a `Name` RHS, or `target==source`).
- Intent:
  - Confirm minimal implementation of reducing from reference boundaries (arguments) to value paths (local declarations) under the same boundary rules as the Rust pilot, even on GC toolchain.emit.
  - Reuse existing runtime-helper contracts (`__pytra_as_list/__pytra_as_dict`) and avoid destructive changes.

## S3-03 Regression Lock Notes (Rust + Kotlin pilots)

- Added tests:
  - `test_py2kotlin_smoke.py::test_ref_container_args_materialize_value_path_with_mutable_copy`
    - Locks behavior that `a: list[int] = xs`, `b: dict[str, int] = ys` become `toMutableList()/toMutableMap()` and not alias assignment.
- Execution checks:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
  - `python3 tools/check_py2kotlin_transpile.py`
  - `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin --ignore-unstable-stdout 18_mini_language_interpreter`

## S4-01 C# Rollout Notes (S4-01-S1-01)

- Changes:
  - Added `current_ref_vars` and container-judgment helpers in `cs_emitter`, and track container-type function arguments as `container_ref_boundary`.
  - In `AnnAssign/Assign` initialization/re-assignment, when RHS is a ref-boundary `Name` and LHS hints a container type:
    - `list[T] -> new List<T>(src)`
    - `dict[K,V] -> new Dictionary<K,V>(src)`
    - `set[T] -> new HashSet<T>(src)`
    - `bytes/bytearray -> new List<byte>(src)`
    are applied to materialize value paths.
  - Added `test_ref_container_args_materialize_value_path_with_copy_ctor` to `test_py2cs_smoke` to detect alias-assignment recurrence.
- Validation:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v` (PASS)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cs --ignore-unstable-stdout 18_mini_language_interpreter` (PASS)
  - `python3 tools/check_py2cs_transpile.py` still fails on 2 known unsupported fixtures (`Yield` / `Swap`) (no new regression from this change).

## S4-01 JS/TS Rollout Notes (S4-01-S2-01)

- Changes:
  - Added `current_ref_vars` and container-judgment helpers in `js_emitter`, and track container-type function arguments as `container_ref_boundary`.
  - In `AnnAssign/Assign` initialization/re-assignment, when RHS is a ref-boundary `Name` and LHS hints a container type:
    - `list/tuple/bytes/bytearray`: `Array.isArray(src) ? src.slice() : Array.from(src)`
    - `dict`: `{ ...src }` (fallback `{}` for non-object)
    - `set`: `new Set(src)` (fallback empty set for non-Set)
    are applied to materialize value paths.
  - Added ref-container regressions to `test_py2js_smoke` / `test_py2ts_smoke`, locking identical output also for TS preview (JS pipeline).
- Validation:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v` (PASS)
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v` (PASS)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets js,ts --ignore-unstable-stdout 18_mini_language_interpreter` (PASS)
  - `python3 tools/check_py2js_transpile.py` / `check_py2ts_transpile.py` stop at pre-step `east3-contract` with `FAIL cs: src/py2cs.py missing ['choices=["2", "3"]']` (common blocker outside JS/TS implementation diffs).

## S4-01 Go Rollout Notes (S4-01-S3-01)

- Changes:
  - Added `ref_vars` context in `go_native_emitter`, and track function-argument container types as `container_ref_boundary`.
  - In `AnnAssign/Assign` initialization/re-assignment, when RHS is a ref-boundary `Name` and LHS is a container type:
    - slice: `append([]T(nil), src...)`
    - map: IIFE + `make(map[K]V, len(src))` + `range` copy (`nil` remains `nil`)
    are applied to materialize local value paths.
  - Added `test_ref_container_args_materialize_value_path_with_copy_expr` to `test_py2go_smoke` to detect alias-assignment recurrence.
- Validation:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v` (PASS)
  - `python3 tools/check_py2go_transpile.py` (PASS)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets go --ignore-unstable-stdout 18_mini_language_interpreter` remains `run_failed` on existing Go-generated `TokenLike` field resolution failure (blocker outside this task).

Breakdown:
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] Inventory current container ownership models by backend (value/reference/GC/ARC) and create a gap matrix.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] Specify common terms and judgment rules for "reference-management boundary", "typed/non-escape reduction", and "escape conditions".
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] Create minimal extension design to retain/propagate container ownership hints in EAST3 node metadata.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] Define backend-neutral ownership decision APIs available in `CodeEmitter` base.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Implement pilot in Rust backend and add split between `object` boundary and typed value paths.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] Implement pilot in a GC backend (Java or Kotlin) and verify reduction under the same rules.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] Add regression tests for the two pilot backends (unit + sample fragments) and lock recurrence detection.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] Roll out sequentially to `cs/js/ts/go/swift/ruby/lua` and absorb runtime-dependency differences per backend.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S1-01] Roll out to C# backend and materialize ref-boundary argument containers into value paths using copy constructors.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S2-01] Roll out the same judgment rules to dynamic-container helper boundaries on JS/TS toolchain.emit.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S3-01] Roll out to Go backend and separate `any` boundaries from typed value paths.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S4-01] Roll out to Swift backend and separate `Any` boundaries from typed value paths.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S5-01] Roll out to Ruby backend and add materialization rules for dynamic-helper boundaries and local value paths.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S6-01] Roll out to Lua backend and add materialization rules for table-helper boundaries and local value paths.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] Run parity/smoke to confirm non-regression, and record unmet items separately as blockers.
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] Add operation rules (reference-management boundary and rollback procedure) to `docs/ja/how-to-use.md` and backend specs.

Decision Log:
- 2026-03-01: Per user request, newly created P3 plan to roll out the container reference-management policy already adopted in C++ to non-C++ toolchain.emit.
- 2026-03-01: Chosen policy is not "force-port `rc` to each language," but "unify abstract rules: dynamic boundaries use reference management; typed known non-escape paths use value types."
- 2026-03-02: As S1-01, audited the current non-C++ backend models and organized that `rs/cs/go/java/kotlin/swift` are centered on "typed containers + Any/Object fallback," while `js/ts/ruby/lua` are centered on "dynamic containers + runtime helpers."
- 2026-03-02: As S1-02, defined `container_ref_boundary` / `typed_non_escape_value_path` / `escape_condition` as v1 terms, and fixed fail-closed policy to treat unjudgeable cases as escape.
- 2026-03-02: As S2-01, defined the EAST3 `container_ownership_hints_v1` schema and node reference key (`meta.container_ownership_hint_ref`), and fixed propagation/promotion/fail-closed rules.
- 2026-03-02: As S2-02, defined a base ownership-judgment API proposal for CodeEmitter and clarified the boundary between base responsibilities (judgment) and backend responsibilities (representation mapping).
- 2026-03-02: As S3-01, implemented `to_vec()/clone()` materialization from reference arguments to value-typed locals in the Rust emitter, adding a pilot that safely routes typed value paths (unit/transpile/parity passed).
- 2026-03-02: As S3-02, implemented `ref_vars` tracking plus `toMutableList()/toMutableMap()` materialization for `AnnAssign/Assign` in the Kotlin emitter, adding a pilot of the same boundary rules on a GC backend.
- 2026-03-02: As S3-03, added Kotlin smoke regressions and confirmed pass through `check_py2kotlin_transpile` + sample parity (case18).
- 2026-03-02: Added S4-01 split; as S4-01-S1-01, implemented copy-constructor materialization for C# backend. `test_py2cs_smoke` and sample parity (case18) passed; `check_py2cs_transpile` `Yield/Swap` failures remain known.
- 2026-03-02: As S4-01-S2-01, added ref-container materialization in JS emitter (`slice/Array.from`, `{...src}`, `new Set(src)`), reflected simultaneously in TS preview. JS/TS smoke and sample parity (case18) passed; `check_py2js/ts_transpile` failures were separated as common `east3-contract` (C# CLI contract) blockers.
- 2026-03-02: As S4-01-S3-01, added ref-container materialization in Go emitter (slice copy + map deep-copy IIFE). Go smoke/transpile passed; `sample/18` parity(go) `run_failed` was separated into S4-02 blockers as the existing `TokenLike` field resolution failure.
- 2026-03-02: As S4-01-S4-01, added `ref_vars` tracking and container materialization for `AnnAssign/Assign` in Swift emitter (`Array(__pytra_as_list(...))` / `Dictionary(uniqueKeysWithValues: __pytra_as_dict(...).map { ... })`). `test_py2swift_smoke` / `check_py2swift_transpile` passed; sample parity(case18) was `toolchain_missing` skip with no new `run_failed`.
- 2026-03-02: As S4-01-S5-01, added `ref_vars` + `decl_type`-based container materialization in Ruby emitter (`__pytra_as_list(...).dup` / `__pytra_as_dict(...).dup`) and updated `dict.get` lowering to `Hash#fetch`. `test_py2rb_smoke` passed; `sample/18` parity(ruby) `run_failed` caused by existing `single_char_token_tags` init gap was separated into S4-02 blockers.
- 2026-03-02: As S4-01-S6-01, introduced function-scope `ref_vars/type_map` in Lua emitter and materialized ref-boundary containers in `AnnAssign/Assign(Name)` into shallow copies (list: index walk, dict: `pairs` walk). Added regressions passed, and `check_py2lua_transpile` + sample/18 parity(lua) passed (`test_py2lua_smoke` global existing expectation diffs were separated in S4-02).
- 2026-03-02: Ran S4-02 and cross-checked `check_py2{cs/js/ts/go/swift/rb/lua}_transpile` plus sample parity(case18). Separated blockers: `go`=`TokenLike` field compile error, `ruby`=tokenize `run_failed`, `swift`=`toolchain_missing` skip, and known fixture/contract failures on `cs/rb/js/ts` transpile.
- 2026-03-02: As S5-01, added non-C++ backend reference-boundary operation rules (validation commands/rollback) to `docs/ja/how-to-use.md`, and reflected the same v1 contract in `spec-gsk-native-backend.md` / `spec-ruby-native-backend.md` / `spec-lua-native-backend.md`.
