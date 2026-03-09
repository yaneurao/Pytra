# P2: Typed Compiler Boundaries and Retreat of Internal Object Carriers

Last updated: 2026-03-09

Related TODO:
- `ID: P2-COMPILER-TYPED-BOUNDARY-01` in `docs/ja/todo/index.md`

Background:
- Pytra mainly targets typed Python, but compiler/selfhost internal boundaries still widely rely on `dict[str, object]`, `list[object]`, and `make_object(...)`.
- In the current selfhost stage1 path, `transpile_cli`, `backend_registry_static`, and generated selfhost parser artifacts still move compiler documents, backend specs, option payloads, and AST nodes through generic object carriers.
- That was useful as bootstrap scaffolding, but it no longer matches the typed-Python implementation philosophy and blocks retreating `make_object` out of compiler-internal lanes.
- Before removing `make_object` more aggressively, the compiler boundaries themselves must first move to typed carriers; otherwise the selfhost/compiler path breaks wholesale.

Goal:
- Move compiler/selfhost internal boundaries to nominal typed carriers and push `dict[str, object]`, `list[object]`, and `make_object(...)` back into backend/runtime implementation details.
- Restrict `make_object`, `py_to`, and `obj_to_*` to user-facing `Any/object` boundaries or explicit adapter seams, and stop using them for known-schema compiler internals.
- Make the "typed Python is the source of truth" policy consistent inside selfhost/compiler implementation boundaries too.

Scope:
- `src/toolchain/frontends/transpile_cli.py` and its selfhost-expanded artifacts
- `src/runtime/cpp/native/compiler/{transpile_cli,backend_registry_static}.{h,cpp}`
- `src/runtime/cpp/generated/compiler/*` and `selfhost/runtime/cpp/pytra-gen/compiler/*`
- Selfhost parser / EAST builder paths around `src/toolchain/ir/core.py`
- Docs / guards / regression tests for compiler boundaries

Out of scope:
- Removing user-facing `Any/object` functionality itself
- Deleting the `make_object` overload family from `py_runtime.h` in one shot
- Fully removing the stage1 selfhost host-Python bridge in this plan alone
- Redesigning the entire C++ runtime

## Mandatory Rules

These are requirements, not recommendations.

1. Any compiler-internal payload with a known schema must use a nominal typed carrier (class / dataclass / typed record), not `dict[str, object]`.
2. `dict[str, object]` and `list[object]` are allowed only at explicit seams such as JSON decode, extern/hooks, and legacy compatibility adapters. They must not flow through internal logic by default.
3. The selfhost parser / EAST builder must not keep raw `dict<str, object>{{...}}` assembly as the canonical path. Typed node constructors or typed builder helpers must become the source of truth.
4. Dynamic JSON values used inside the compiler must be isolated behind a dedicated nominal type such as `JsonValue`, not by expanding generic object helpers.
5. Compiler-side `make_object`, `py_to`, and `obj_to_*` usage may remain only when it can be classified as `user_boundary`, `json_adapter`, or `legacy_migration_adapter`. Unclassified usage must not remain as hidden debt.
6. Do not add new generic carriers during the migration. If a legacy adapter remains temporarily, its removal step must be recorded in the plan / decision log.
7. Backends/runtimes must not paper over missing typed-boundary work by adding more object fallback helpers. Required type information must be fixed upstream in frontend/lowering/builder lanes.

Acceptance criteria:
- Canonical compiler entrypoints such as `load_east3_document` use a typed root carrier as the source of truth rather than raw `dict[str, object]`.
- `backend_registry_static` passes backend specs, layer options, and IR through typed carriers plus explicit adapters rather than default raw object dict transport.
- In the selfhost parser / generated compiler path, checked-in AST nodes are no longer directly assembled through `dict<str, object>{{... make_object(...) ...}}` paths.
- Remaining compiler-lane `make_object` / `py_to` usage is explicitly classified and limited to user-facing `Any/object` boundaries or adapter seams.
- Guards/tests exist so typed-boundary regressions fail fast.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 -m unittest discover -s test/unit/selfhost -p 'test_selfhost_virtual_dispatch_regression.py'`
- `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`
- `git diff --check`

## Implementation Order

Keep the order fixed: decide the typed contract first, add adapters second, then peel raw object assembly out of selfhost-generated artifacts.

1. Inventory and classification
2. Lock the typed end state
3. Introduce typed carriers in the Python source of truth
4. Mirror them into generated/native compiler interfaces
5. Retire raw object assembly from selfhost parser / EAST builder
6. Isolate JSON / hook / legacy adapters
7. Add guards / regressions / archive updates

## Breakdown

- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] Inventory remaining `dict[str, object]`, `list[object]`, `make_object`, and `py_to` usage across `transpile_cli`, `backend_registry_static`, selfhost parser paths, and generated compiler runtime, then classify each usage as `compiler_internal`, `json_adapter`, `extern_hook`, or `legacy_bridge`.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] Lock the typed-boundary contract and non-goals in the decision log so they stay consistent with `spec-dev`, `spec-runtime`, and `spec-boxing`.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] Define typed carrier specs for compiler root payloads (EAST document, backend spec, layer options, emit request/result).
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Introduce typed carriers and thin legacy adapters in the Python source of truth (`transpile_cli.py`, registry helpers, builder helpers).
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] Introduce typed carrier mirrors or typed wrapper APIs in the C++ selfhost/native compiler interfaces and reduce raw `dict<str, object>` exchange.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Move selfhost parser / EAST builder node construction onto typed constructors / builder helpers and gradually retire direct `dict<str, object>{{...}}` assembly.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Retreat remaining `make_object` usage in generated compiler / selfhost runtime down to serialization/export seams only.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Separate JSON, extern/hooks, and other intentionally dynamic carriers from the compiler typed model behind `JsonValue` or explicit adapters.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] Label every remaining `make_object` / `py_to` / `obj_to_*` usage and add guards that reject uncategorized reintroduction.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] Refresh selfhost build/diff/prepare/bridge regressions and lock non-regression after the typed-boundary changes.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] Update docs / TODO / archive and record whether each remaining `make_object` usage is `user boundary only` or `explicit adapter only`.

## Expected Deliverables

### Deliverables for S1

- A concrete inventory of which files/usages still keep forbidden generic carriers inside compiler internals.
- A written explanation of why this P2 does not mean "delete `make_object` everywhere" and what counts as completion.

### Deliverables for S2

- `transpile_cli` and `backend_registry_static` treat typed payloads as the canonical path.
- Legacy `dict[str, object]` APIs remain only as thin adapters so callers can move gradually.

### Deliverables for S3

- The selfhost parser / EAST builder uses nominal node builders.
- Checked-in compiler paths stop spelling out repeated `make_object("kind")` / `make_object(value)` AST assembly.

### Deliverables for S4

- Only genuinely dynamic paths such as `JsonValue` or extern/hook adapters keep object carriers.
- Remaining compiler-internal generic carriers are all justified and classifiable.

### Deliverables for S5

- Selfhost regressions and audits can detect any collapse back to generic compiler carriers.
- The end state is traceable in docs/TODO/archive.

Decision log:
- 2026-03-09: Added this P2 in response to the user request to prioritize typed compiler boundaries over trying to delete `make_object` directly.
- 2026-03-09: Fixed the policy that user-facing `Any/object` boundaries remain part of the current language/runtime contract; this P2 focuses on compiler/selfhost internal dynamic-carrier cleanup instead.
- 2026-03-09: Fixed the policy that removing the stage1 selfhost host-Python bridge is out of scope here and should be tackled only after typed carriers exist.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: Classified `json_adapter` first and kept it limited to explicit JSON root decode/encode seams. Representative sites are the `.json` input lane in `src/toolchain/frontends/transpile_cli.py::load_east_document()` where `json.loads_obj(...).raw` is normalized into the EAST root, `src/runtime/cpp/native/compiler/transpile_cli.cpp::_load_json_root_dict()`, and `src/runtime/cpp/native/compiler/backend_registry_static.cpp::emit_source()` where `ir` is serialized via `json.dumps(make_object(ir))` before calling host Python. These lanes may remain only as the last adapter seam after typed carriers exist.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: Fixed `legacy_bridge` to mean "raw object-dict APIs that stay public even though the payload can be typed." Representative sites are `src/toolchain/frontends/transpile_cli.py::load_east_document()` wrapping `east_any` into `{\"east\": east_any}` and forcing it back through `dict_any_get_dict(...)`, the public `load_east3_document(...) -> dict<str, object>` surface in `src/runtime/cpp/native/compiler/transpile_cli.h/.cpp`, and the mirrored `dict_any_get*` helpers in `selfhost/py2cpp.py` that `tools/prepare_selfhost_source.py` exports into the selfhost seed. P2 should push this category into thin adapters and remove it from canonical internal flow.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: Fixed `compiler_internal` to cover payloads whose schema is already known but still travel through generic carriers. Representative sites are the `dict[str, dict[str, object]]` signature map returned by `src/toolchain/frontends/transpile_cli.py::extract_function_signatures_from_python_source()`, `get_backend_spec()` / `resolve_layer_options()` / `lower_ir()` / `optimize_ir()` in `src/runtime/cpp/native/compiler/backend_registry_static.cpp`, the source-of-truth node/module builders in `src/toolchain/ir/core.py`, and the selfhost generated parser paths in `selfhost/runtime/cpp/pytra-gen/compiler/east_parts/core.cpp` where `_sh_append_fstring_literal()`, `_sh_parse_def_sig()`, and the module root still assemble AST/meta via `dict<str, object>{{... make_object(...) ...}}`. S2-S3 should replace this category with typed carriers and typed builders.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: Fixed `extern_hook` to mean the explicit dynamic seams used to strip or route `@extern`-driven payloads. Representative sites are `_is_extern_call_expr()`, `_is_extern_function_decl()`, `_is_extern_variable_decl()`, and `_build_cpp_emit_module_without_extern_decls()` in `selfhost/py2cpp.py`, plus `apply_runtime_hook(...)` in `src/runtime/cpp/native/compiler/backend_registry_static.cpp`. These are not canonical typed compiler payload flow and should stay isolated with the other dynamic adapters in S4.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: Aligned with `spec-boxing` and fixed the non-goal that P2 does not remove the `Any/object` boundary itself. `make_object(...)`, `obj_to_*`, and `py_to_*` remain part of the user-facing `Any/object` contract; P2 only retreats the compiler/selfhost lanes where the schema is already known but still routed through raw object carriers.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: Aligned with `spec-runtime` / `spec-dev` and fixed the rule that JSON dynamics must not justify broader generic-object helpers. Raw `dict[str, object]` / `list[object]` may remain only at explicit JSON root decode/encode seams; the long-term canonical lane is `JsonValue` / `JsonObj` / `JsonArr`. Typed-boundary gaps must not be rescued by adding helper fallbacks such as `sum(object)` or `zip(object, object)`.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: Following `spec-dev`, typed-boundary meaning stays frontend/lowering-owned and must not be reinterpreted by backend/hook/native runtime from raw dicts or callee names. `type_expr` remains the source of truth for type meaning, `resolved_type` remains a mirror, and `meta.dispatch_mode` stays a once-fixed compile input. During the migration, backend/runtime silent fallback or re-deciding these semantics is forbidden.
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: The `ModuleArtifact.metadata` / `ProgramArtifact.writer_options` object slots from `spec-dev` remain allowed only as bounded target-local leaf payloads. They are not justification for keeping whole compiler root payloads on raw `dict[str, object]` transport. P2 types the known-schema lanes first (EAST root, backend spec, layer options, emit request/result), while full nominal-ADT rollout and full stage1 host-Python-bridge removal remain separate non-goals.
