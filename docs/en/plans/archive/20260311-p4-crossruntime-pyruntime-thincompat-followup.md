<a href="../../../ja/plans/archive/20260311-p4-crossruntime-pyruntime-thincompat-followup.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4: Classify final thin-compat dependencies across the C++/Rust/C# emitters

Last updated: 2026-03-11

Related TODO:
- `ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01` in `docs/en/todo/index.md`

Background:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` and `P1-CPP-PYRUNTIME-HEADER-SHRINK-01` reduced `src/runtime/cpp/native/core/py_runtime.h` down to object-bridge mutation helpers plus the final two thin compatibility helpers: template `py_runtime_type_id` and `py_isinstance`.
- Shrinking the header any further now depends on separating the generic `py_isinstance(...)` blockers that remain in the C++ emitter from the shared `type_id` API residual that Rust/C# still expose.
- The archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` aligned the broader residual contract, but it did not track the specific blockers for removing the final thin compatibility helpers.

Goal:
- Separate the emitter-side blockers that prevent removing the final two thin compatibility helpers from the cross-runtime shared API residual that must be handled later.
- Lock the end state and bundle-sized removal order for those residuals in docs, tooling, and representative smoke/contract checks.

Scope:
- `src/backends/cpp/emitter/runtime_expr.py`
- `src/backends/cpp/emitter/stmt.py`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- `tools/check/check_crossruntime_pyruntime_thincompat_inventory.py`
- `tools/unittest/tooling/test_check_crossruntime_pyruntime_thincompat_inventory.py`
- As needed, `tools/unittest/emit/cpp/test_east3_cpp_bridge.py`
- As needed, `tools/unittest/emit/rs/test_py2rs_smoke.py`
- As needed, `tools/unittest/emit/cs/test_py2cs_smoke.py`

Out of scope:
- Immediately removing more code from `py_runtime.h` itself
- Full runtime-mirror redesign for Rust/C#/C++
- Full regeneration / final cleanup of every generated C++ stdlib lane
- Changing the `Any/object` boundary or the `type_id` semantics themselves

Acceptance criteria:
- The emitter-side final thin-compat blockers are inventory-classified and uncategorized reintroduction fails fast.
- The boundary between `cpp_header_thincompat_blocker` and `crossruntime_shared_type_id_api` is locked in docs/tests/tooling.
- Representative C++/Rust/C# smoke or contract checks pass.
- At least one bundle completes the inventory/source-guard/docs work for these blockers.

End state:
- `cpp_header_thincompat_blocker`: only the generic helper calls that directly block removing the final thin C++ header helpers remain in this bucket. The initial state is the two `py_isinstance` call sites in `runtime_expr.py` and `stmt.py`.
- `crossruntime_shared_type_id_api`: Rust/C# emitters should no longer emit the generic names directly. Instead they should use the thin helper naming `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`. The generic `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` names may remain only as internal runtime aliases.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_crossruntime_pyruntime_thincompat_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_crossruntime_pyruntime_thincompat_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Breakdown:
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S1-01] Inventory the final thin-compat blockers into `cpp_header_thincompat_blocker` and `crossruntime_shared_type_id_api`, then add tooling/tests.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S1-02] Lock the end state and bundle-sized removal order in docs/source guards.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S2-01] Move the C++ emitter `py_isinstance` blocker lanes onto explicit helpers and shrink `cpp_header_thincompat_blocker`.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S2-02] Align Rust/C# shared `type_id` API residuals to the intended naming/bridge end state and document the remaining non-blockers.
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S3-01] Refresh representative smoke/tests/docs and archive the task.

Decision log:
- 2026-03-11: Opened immediately after archiving `P1-CPP-PYRUNTIME-HEADER-SHRINK-01`, once the C++ header was down to object-bridge helpers plus the final thin `py_runtime_type_id` / `py_isinstance` compatibility surface.
- 2026-03-11: As `S1-01`, added `tools/check/check_crossruntime_pyruntime_thincompat_inventory.py` plus unit coverage and bucketed the two C++ `py_isinstance` blockers separately from the Rust/C# shared `type_id` API residuals.
- 2026-03-11: As `S1-02`, fixed the end state as “`cpp_header_thincompat_blocker` should become an empty bucket, while Rust/C# remain isolated in `crossruntime_shared_type_id_api` until the naming/bridge follow-up.”
- 2026-03-11: As `S2-01`, retargeted the two generic C++ `py_isinstance` sites in `runtime_expr.py` and `stmt.py` onto `py_runtime_object_isinstance`, leaving `cpp_header_thincompat_blocker` empty.
- 2026-03-11: As `S2-02`, aligned the Rust/C# renderer surface to `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`, and switched the inventory from raw file-wide regex matching to render-surface helper classification. The old generic names remain only as internal runtime aliases and are treated as non-blockers.
- 2026-03-11: As `S3-01`, re-ran the representative inventory/tooling and C++/Rust/C# smoke lanes, then moved the thincompat follow-up docs into archive so the active TODO can close cleanly.
