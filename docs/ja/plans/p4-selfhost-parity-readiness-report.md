# P4 Selfhost Parity Readiness Report

最終更新: 2026-03-11

関連計画:
- [P4 backend_registry の正本化と selfhost parity gate の強化](./archive/20260311-p4-backend-registry-selfhost-parity-hardening.md)

目的:
- representative selfhost gate の実行入口を 1 箇所にまとめる。
- `known_block` と `regression` の見分け方を shared summary vocabulary 単位で確認できるようにする。
- backend readiness を「どの gate を通せばよいか」という実務手順で追えるようにする。

## Representative Gate

### 1. C++ stage1 build

- コマンド: `python3 tools/build_selfhost.py`
- 目的: current Python 実装から C++ selfhost binary を再生成し、最低限の stage1 build を通す。
- 主な失敗:
  - `regression/build_fail`
  - `known_block/not_implemented`

### 2. C++ stage2 build / diff

- コマンド: `python3 tools/build_selfhost_stage2.py`
- コマンド: `python3 tools/check_selfhost_cpp_diff.py`
- 目的: stage1 生成物から stage2 を作り、artifact diff が expected block か regression かを分類する。
- 主な失敗:
  - `known_block/not_implemented`
  - `known_block/unsupported_by_design`
  - `regression/stage2_diff_fail`
  - `regression/stage2_transpile_fail`

### 3. C++ direct end-to-end parity

- コマンド: `python3 tools/verify_selfhost_end_to_end.py`
- 目的: representative sample で selfhost binary の stdout parity を確認する。
- 主な失敗:
  - `known_block/not_implemented`
  - `known_block/preview_only`
  - `known_block/unsupported_by_design`
  - `regression/direct_compile_fail`
  - `regression/direct_run_fail`
  - `regression/direct_parity_fail`

### 4. Multilang selfhost readiness

- コマンド: `python3 tools/check_multilang_selfhost_suite.py`
- 目的: non-C++ targets の stage1 / multistage readiness を summary block で確認する。
- 主な detail:
  - `pass`
  - `known_block/preview_only`
  - `known_block/unsupported_by_design`
  - `toolchain_missing/toolchain_missing`
  - `regression/self_retranspile_fail`

## Shared Category Contract

top-level category:
- `pass`
- `known_block`
- `toolchain_missing`
- `regression`

detail category:
- `not_implemented`
- `preview_only`
- `unsupported_by_design`
- `known_block`
- `blocked`
- `toolchain_missing`
- `stage2_diff_fail`
- `stage2_transpile_fail`
- `direct_compile_fail`
- `direct_run_fail`
- `direct_parity_fail`
- `self_retranspile_fail`

shared source:
- [backend_registry_diagnostics.py](/workspace/Pytra/src/toolchain/compiler/backend_registry_diagnostics.py)
- [selfhost_parity_summary.py](/workspace/Pytra/tools/selfhost_parity_summary.py)

## Current Readiness Reading

- `known_block/not_implemented`: 実装段階の gap。直近で regression 扱いしてはいけないが、恒久化もしない。
- `known_block/preview_only`: preview backend / preview route であることが明示されている lane。
- `known_block/unsupported_by_design`: 現時点で対象外の lane。multilang runner 未定義や unsupported target を含む。
- `toolchain_missing/toolchain_missing`: ローカル環境不足。backend quality とは分離して扱う。
- `regression/*`: 以前の representative lane と同じ contract で失敗している。優先的に triage する。

## Current Snapshot (2026-03-11)

- C++ `stage2_diff`: `pass / pass`
- C++ `direct_e2e`: `pass / pass`
- multilang `stage1`: `rs/cs/js/ts/go/java/swift/kotlin` がすべて `fail / unknown / skip`
- multilang `multistage`: 同 8 target がすべて `stage1_transpile_fail`

関連 status:
- [P1-MQ-04 Stage1 Status](./p1-multilang-selfhost-status.md)
- [P1-MQ-05 Multistage Selfhost Status](./p1-multilang-selfhost-multistage-status.md)

## Routine Check Order

1. `python3 tools/check_todo_priority.py`
2. `python3 tools/check_selfhost_contract_reentry_guard.py`
3. `python3 tools/build_selfhost.py`
4. `python3 tools/build_selfhost_stage2.py`
5. `python3 tools/check_selfhost_cpp_diff.py`
6. `python3 tools/verify_selfhost_end_to_end.py`
7. `python3 tools/check_multilang_selfhost_suite.py`

補足:
- `python3 tools/check_transpiler_version_gate.py` は transpiler 変更時に必ず実行する。
- representative change では `test/unit/selfhost/*.py` と `test/unit/common/test_py2x_entrypoints_contract.py` を先に通す。
- `python3 tools/check_selfhost_contract_reentry_guard.py` は representative internal change 向けの共通 host/selfhost contract gate で、`run_local_ci.py` にも組み込まれている。

## Archive Handoff

- P4 全体が完了したら、この report だけを孤立させず、対応する plan と同じ完了日で archive へ移す。
- plan 本体は `docs/ja/plans/archive/YYYYMMDD-<task-group>.md` へ移動する。
- TODO 側は `docs/ja/todo/archive/index.md` と `docs/ja/todo/archive/YYYYMMDD.md` に同じ完了文脈を残す。
- readiness report を残す場合も、archive 側から辿れるように相互リンクを張る。
