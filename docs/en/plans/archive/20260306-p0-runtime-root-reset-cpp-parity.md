<a href="../../../ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: runtime-root reset (`runtime2` quarantine + new `runtime/`) and C++ parity recovery

Last updated: 2026-03-06

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-RUNTIME-ROOT-RESET-CPP-01`
- Archived from live `plans/` on 2026-03-14 by `P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01`

Background:
- Runtime implementation work moved ahead before the ABI boundary had settled, so responsibility leaks kept reappearing from runtime code back into emitters.
- The old three-layer C++ runtime shape (`pytra/`, `pytra-core/`, `pytra-gen/`) had ambiguous ownership, and the `pytra/` shim had become pure maintenance debt.
- The design direction at the time fixed the runtime layout to two layers: handwritten `core/` plus SoT-generated `gen/`.
- To reduce migration risk, the old tree was first quarantined under `src/runtime2/`, then a new `src/runtime/` was rebuilt in stages.
- The first milestone was C++ parity recovery; other languages were intentionally deferred.

Objective:
- Quarantine the legacy runtime and rebuild a clean `src/runtime/`.
- Collapse the C++ runtime to `src/runtime/cpp/core` plus `src/runtime/cpp/gen`, with no `pytra` shim.
- Restore C++ fixture/sample parity, including artifact-size and CRC checks.

In scope:
- `src/runtime` rename/rebuild
- C++ runtime path references in `src/backends/cpp/*`
- C++ runtime copy/build paths in `src/toolchain/compiler/*`
- C++ runtime generation in `tools/gen/gen_runtime_from_manifest.py` and related manifest data
- C++ parity execution flow in `tools/check/runtime_parity_check.py`
- Runtime-path wording in the relevant docs/specs

Out of scope:
- Runtime migration for non-C++ backends
- Runtime API expansion
- Performance optimization work

Acceptance criteria:
- The legacy runtime is quarantined under `src/runtime2/`, and new implementation paths reference only `src/runtime/`.
- `src/runtime/cpp/` uses only `core/` and `gen/`, with no active `pytra/` shim.
- C++ runtime references are unified on `runtime/cpp/core` plus `runtime/cpp/gen`.
- `tools/check/runtime_parity_check.py --targets cpp --case-root fixture` passes.
- `tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples` passes.

Validation commands:
- `python3 tools/check/check_todo_priority.py`
- `rg -n "runtime/cpp/pytra|src/runtime2" src/backends/cpp src/toolchain tools`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## Breakdown

- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-01] Inventoried all C++ runtime reference points across backend/toolchain/tools and fixed the migration blast radius.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-02] Moved `src/runtime` to `src/runtime2` and created the new `src/runtime/cpp/{core,gen}` tree.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-03] Added a guard that forbids references to `src/runtime2`.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-01] Updated C++ backend runtime/include resolution to the `core/gen` layout and removed the `pytra` shim route.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-02] Switched C++ runtime generation output to `runtime/cpp/gen`.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-03] Unified the C++ build manifest/copy path on `runtime/cpp/core` plus `runtime/cpp/gen`.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-01] Regenerated required C++ runtime modules (`std/utils`) from SoT into `gen/` only.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-02] Reorganized handwritten C++-specific implementation into `core/`.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-01] Passed fixture parity.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-02] Passed sample parity.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-03] Eliminated the remaining parity failures and reconfirmed stable passing results.
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S5-01] Updated runtime-layout docs and operating procedures.

Decision log:
- 2026-03-05: Adopted the "quarantine `src/runtime` into `src/runtime2`, then rebuild `src/runtime`" plan and limited the first rollout to C++ parity recovery.
- 2026-03-05: Fixed the migration order to `(1) backend include/runtime paths, (2) toolchain copy/build manifest, (3) tooling guards and parity scripts`.
- 2026-03-05: Moved the legacy tree aside, rebuilt `src/runtime/cpp/{core,gen}`, and isolated the old shim under `src/runtime2/cpp/pytra`.
- 2026-03-05: Regenerated SoT-owned C++ runtime modules into `gen/`, moved handwritten C++ pieces into `core/`, and updated layout guards to the new two-lane ownership model.
- 2026-03-05: Passed fixture parity, then cleared the remaining GIF/sample mismatches by fixing `math.pi/e` initialization and reran all sample parity cases to green.
