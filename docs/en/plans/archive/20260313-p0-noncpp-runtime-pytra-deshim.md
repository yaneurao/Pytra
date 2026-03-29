<a href="../../../ja/plans/archive/20260313-p0-noncpp-runtime-pytra-deshim.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Remove all checked-in non-C++/non-C# runtime `pytra/` lanes

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` item `ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01`

Background:
- As of 2026-03-13, the checked-in tree still contains `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**`.
- The archived plan `20260313-p1-noncpp-runtime-layout-rollout-remaining.md` was completed under the assumption that some non-C++ backends could keep `pytra/` as a public shim / compatibility lane.
- The current user instruction supersedes that assumption: except for C++ and C#, all checked-in `src/runtime/<lang>/pytra/**` must disappear, and the permanent repo-owned runtime layout must be limited to `generated/native`.
- Current PHP/Lua/Ruby smoke, packaging, and contract checks still assume repo-tree direct loads from `pytra/**` or compat shim inventory, so that gap is still unresolved.
- C# already deleted its duplicate lane; Rust and the remaining backends still keep checked-in `pytra/` directories.

Goal:
- Remove checked-in `src/runtime/<lang>/pytra/**` from every non-C++/non-C# backend (`rs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php`).
- Make `generated/native` the only permanent repo-owned runtime layout vocabulary.
- Even when public compatibility is still needed, move compat wrappers out of checked-in `src/runtime/**` and into output staging / packaging / generated artifacts.
- Sync contracts, guards, smoke tests, and docs to the new policy, and fail fast if checked-in `pytra/` returns.

Scope:
- `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- `src/toolchain/compiler/js_runtime_shims.py`
- selfhost / packaging / transpile output / runtime copy flows
- `tools/check/check_noncpp_runtime_layout_contract.py`
- `tools/check/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- runtime layout / marker / naming / SoT guards
- representative backend smoke / tooling unit / docs / TODO

Out of scope:
- Redesigning the C++ runtime packaging / shim tree
- Reworking the already-finished C# duplicate lane cleanup
- Changing the ownership model of `generated/**` / `native/**` themselves
- Changing the behavior of canonical sources under `src/pytra/**`
- Immediately banning all output-side compat wrappers

Acceptance criteria:
- `find src/runtime -maxdepth 2 -type d -name pytra | sort` returns only `src/runtime/cpp/pytra` in the checked-in tree.
- `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**` no longer exists, including directories.
- `tools/check/check_noncpp_runtime_layout_contract.py` and `tools/check/check_noncpp_runtime_layout_rollout_remaining_contract.py` no longer treat checked-in `pytra/**` as compat lanes for these backends and fail fast if they reappear.
- Repo-tree direct-load / source-reexport smoke no longer assumes `src/runtime/<lang>/pytra/**`.
- Backend registry / selfhost / packaging / transpile output contracts are resolved through `generated/native` or output-side staging artifacts only.
- Old `pytra/` compat-lane wording remains only in archived documents, not in active plans, TODO, specs, or checkers.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `find src/runtime -maxdepth 2 -type d -name pytra | sort`
- `python3 tools/check/check_noncpp_runtime_layout_contract.py`
- `python3 tools/check/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check/check_runtime_core_gen_markers.py`
- `python3 tools/check/check_runtime_pytra_gen_naming.py`
- `python3 tools/check/check_runtime_std_sot_guard.py`
- `python3 tools/check/check_multilang_selfhost_stage1.py`
- `python3 tools/check/check_multilang_selfhost_multistage.py`
- `git diff --check`

Implementation policy:
1. The checked-in repo tree may only use `generated/native` as canonical and allowed runtime lanes. For all target backends, `pytra/` is a delete target, not a temporary compat lane.
2. When a dependency still points at `pytra/**`, fix it by switching to `generated/native` directly or by moving the minimal compatibility surface into output-side artifacts, not by keeping repo-tree shims.
3. Repo-tree direct-load smoke is itself an incorrect layout contract and must be replaced by smoke that validates `generated/native` or output staging.
4. Rust is handled first as its own cleanup slice because of the remaining `rs/cs` residual contract, then the rest proceeds in static-family and script-family bundles.
5. Archive documents remain as history, but active policy is defined only by this P0 and `docs/ja/todo/index.md`.

## Backend grouping

### Rust cleanup

- `rs`

### Static family

- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

### Script family

- `js`
- `ts`
- `lua`
- `ruby`
- `php`

## Breakdown

- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01] Remove checked-in `src/runtime/<lang>/pytra/**` from every non-C++ / non-C# backend and converge the permanent repo-owned runtime layout on `generated/native` only.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01] Lock the current `pytra/**` inventory, references, delete blockers, and current->target mapping for the 12 target backends into plan / contract / checker form.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-02] Switched active contracts / checkers / spec wording to `generated/native only` and made checked-in `pytra/**` re-entry fail fast.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-01] Delete checked-in `src/runtime/rs/pytra/**` for Rust (`rs`) and remove repo-tree `pytra/**` assumptions from `py2rs`, selfhost, runtime guards, and smoke.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-02] Align the static family (`go/java/kotlin/scala/swift/nim`) registry / packaging / smoke / tooling on direct `generated/native` references so checked-in `pytra/**` remains only as deletion inventory.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-03] Physically delete checked-in `src/runtime/<lang>/pytra/**` for the static family and update allowlists / inventory / representative smoke to the deletion end state.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-01] Rework JS/TS import paths, shim writers, selfhost, and smoke so repo-tree `src/runtime/{js,ts}/pytra/**` direct-load and compat contracts disappear.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-02] Move Lua/Ruby/PHP packaging / runtime copy / loader contracts to `generated/native` or output-side staging and remove checked-in `pytra/**` assumptions.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-03] Physically delete checked-in `src/runtime/<lang>/pytra/**` for the script family and update representative smoke plus contract baselines to the deletion end state.
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S4-01] Sync docs / TODO / archive references / inventory and close with the invariant that no checked-in non-C++ / non-C# backend owns `pytra/`.

Decision log:
- 2026-03-13: `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01` locked the current checked-in `pytra/` directory inventory, exact file inventory, and delete blocker references into a dedicated contract/checker/test so the current state is explicit before removal begins.
- 2026-03-13: The active policy cancels the older assumption that non-C++ backends may keep checked-in `pytra/` as compat lanes. Public compatibility, if still needed, must move to output-side staging instead.
- 2026-03-13: S1-02 first bundle aligned `spec-folder/spec-dev` with the `generated/native only` wording and made doc-policy drift fail fast in the checker.
- 2026-03-13: S1-02 second bundle flipped the Rust active contract / layout-guard wording for `pytra` from `compat` to `delete-target debt`, and removed the assumption that checked-in `rs/pytra` is a live compat lane from `noncpp_runtime_layout_contract.py`, `check_rs_runtime_layout.py`, and the dedicated deshim blocker baseline.
- 2026-03-13: S1-02 third bundle updated the Rust user-facing docs (`docs/ja/tutorial/transpiler-cli.md`, `docs/en/how-to-use.md`) to `delete-target debt` wording and added them to the dedicated deshim doc-policy checker. S1-02 stays open because `rollout_remaining_contract` still retains live `pytra` wording.
- 2026-03-13: S1-02 fourth bundle moved the `pytra` rationale and checker message in `noncpp_runtime_layout_rollout_remaining_contract.py` toward `delete-target debt` wording. S1-02 is still open because the schema-level `target_roots=("generated","native","pytra")` and `compat_*` taxonomy remain.
- 2026-03-13: S1-02 fifth bundle flipped the lane ownership values in `noncpp_runtime_layout_rollout_remaining_contract.py` from `compat` to `delete_target`. S1-02 remains open because the schema field names `compat_*` and `target_roots=("generated","native","pytra")` still remain.
- 2026-03-13: S1-02 sixth bundle shrank the live `target_roots` in `noncpp_runtime_layout_rollout_remaining_contract.py` to `("generated","native")` and updated the checker so only `delete_target` lanes may still point at checked-in `pytra/**`. S1-02 remains open because `compat_files` / `compat_modules` and the wave-B helper/iterator names still retain `compat`.
- 2026-03-13: S1-02 seventh bundle replaced the wave-B `compat` helper / iterator naming in `noncpp_runtime_layout_rollout_remaining_contract.py`, its checker, and its tests with `delete_target`. The main remaining S1-02 residue is now the `compat_files` vocabulary in `noncpp_runtime_generated_cpp_baseline_contract.py` and its checker/test.
- 2026-03-13: S1-02 eighth bundle also replaced the `compat_files` vocabulary in `noncpp_runtime_generated_cpp_baseline_contract.py`, its checker, and its tests with `delete_target_files`. With that, the active contract / checker / spec side no longer carries pytra-specific live `compat` wording, so S1-02 was closed.
- 2026-03-13: S1-02 third bundle rewrote `spec-java-native-backend.md`, `spec-lua-native-backend.md`, and `spec-gsk-native-backend.md` to use `src/runtime/<lang>/{generated,native}/` as the live runtime roots, and widened the doc-policy checker to cover those active native-backend specs.
- 2026-03-13: S2-01 physically deleted checked-in `src/runtime/rs/pytra/**` and updated `check_rs_runtime_layout.py` to fail if the Rust `pytra` lane reappears. `noncpp_runtime_pytra_deshim_contract.py`, `noncpp_runtime_layout_contract.py`, `noncpp_runtime_generated_cpp_baseline_contract.py`, and the crossruntime inventory checkers were also aligned to treat the Rust delete-target lane as already removed rather than as current inventory.
- 2026-03-13: S2-02 assumed that `backend_registry_metadata.py` and the representative static-family smoke tests already resolve runtime files from `generated/native`, then removed `pytra` current-lane mappings from `noncpp_runtime_layout_rollout_remaining_contract.py`. Checked-in `pytra/**` now remains only in the explicit `delete_target_files` / `delete_target_modules` inventories, and the static-family `contract_allowlist` blockers were removed from `noncpp_runtime_pytra_deshim_contract.py`.
- 2026-03-13: S2-03 physically deleted `src/runtime/{go,java,kotlin,scala,swift,nim}/pytra/**` and shrank the current directory/file inventory in `noncpp_runtime_pytra_deshim_contract.py` down to the script family only. The static-family delete-target inventory was collapsed to empty in both `noncpp_runtime_generated_cpp_baseline_contract.py` and `noncpp_runtime_layout_rollout_remaining_contract.py`, and the stale Go allowlist entry was removed from `runtime_std_sot_allowlist.txt`.
- 2026-03-13: S2-03 also strengthened the representative `runtime_source_path_is_migrated` smoke tests to assert the end state directly: `generated/native` remains present while checked-in `pytra/**` is absent. In the same bundle, the active static-family runtime-boundary specs (`spec-java-native-backend.md`, `spec-gsk-native-backend.md`) dropped the now-obsolete delete-target debt wording.
- 2026-03-13: S3-01 removed the JS/TS blocker buckets and exact blocker baseline from `noncpp_runtime_pytra_deshim_contract.py` after switching the repo-tree direct-load smoke to output-side generated shim smoke. Checked-in `src/runtime/{js,ts}/pytra/**` now remains only as deletion inventory; repo-tree direct-load / selfhost / compat-contract blockers are considered resolved.
- 2026-03-13: S3-02 replaced the Lua/Ruby/PHP repo-tree direct-load smoke with output-side staging smoke and removed the remaining script-family blocker baseline from `noncpp_runtime_pytra_deshim_contract.py`. The PHP `require_once __DIR__ . '/pytra/py_runtime.php';` rewrite is treated as output-side staging, not a repo-tree blocker.
- 2026-03-13: S3-03 physically deleted `src/runtime/{js,ts,lua,ruby,php}/pytra/**`, collapsed the current directory/file inventory in `noncpp_runtime_pytra_deshim_contract.py` to empty, and set the script-family delete-target inventory to empty in both `noncpp_runtime_layout_rollout_remaining_contract.py` and `noncpp_runtime_generated_cpp_baseline_contract.py`. Representative smoke now asserts the deletion end state directly by requiring output-side staged runtime helpers while confirming the checked-in repo-tree `pytra/**` is absent.
- 2026-03-13: S4-01 aligned the active tutorial/spec wording to the final invariant and moved the plan/TODO entry into the archive. The checked-in tree now keeps `pytra/` only under `src/runtime/cpp/pytra`, and no non-C++ / non-C# backend retains a repo-owned `pytra/**` lane.
