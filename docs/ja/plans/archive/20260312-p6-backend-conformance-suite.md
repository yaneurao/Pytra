<a href="../../../en/plans/archive/20260312-p6-backend-conformance-suite.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6 Backend Conformance Suite

最終更新: 2026-03-12

目的:
- 同じ feature fixture を複数 backend で検証する共通 conformance suite を整備し、backend ごとの差分を個別 smoke test 依存から脱却させる。
- parse / EAST / EAST3 lowering / emit / runtime parity を同じ feature ID に結び付けて追跡できるようにする。
- parity 進捗を「個別の backend smoke がたまたま通る」状態ではなく、feature 単位のテスト制度に変える。

背景:
- いまの backend test は target ごとの smoke が中心で、同じ feature がどの backend でどこまで通るかを横断的に見にくい。
- `P5` で feature contract を固定しても、共通 fixture / harness がなければ drift を早期に検知できない。
- `P5` の `conformance_handoff` manifest を seed にしないと、representative fixture / lane / backend order が task ごとにずれる。
- C++ 先行実装のままでは、他 backend の未対応・劣化・diagnostic 不整合が個別 test の隙間に残りやすい。
- representative lane から始めつつも、将来的に feature × backend の matrix を自動更新できる conformance basis が必要である。

非対象:
- すべての backend で full runtime parity をすぐに達成すること。
- 既存 smoke test の全面置換。
- CI 全体の全面 redesign。

受け入れ基準:
- feature fixture を parse / EAST / EAST3 lowering / emit / runtime parity へ結び付ける共通 harness 追加方針が定義されている。
- representative backend（まず C++ / Rust / C# など）へ接続する test lane が決まっている。
- `pytra.std.*` representative module の runtime parity を backend 横断で比較する方針が決まっている。
- conformance suite の結果を support matrix や docs へ接続する handoff が定義されている。
- `docs/en/` mirror が日本語版と同じ内容に追従している。

## 子タスク

- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S1-01] feature ID と fixture path の対応付け規則を決め、syntax / builtins / `pytra.std.*` representative case を分類する。
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-01] parse / EAST / EAST3 lowering / emit / runtime parity の各 lane をどう共通 harness に結び付けるかを設計する。
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-02] C++ / Rust / C# を first representative lane とする backend-selectable conformance runner の方針を決める。
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S3-01] `pytra.std.*` representative module（例: `json`, `pathlib`, `enum`, `argparse`）の runtime parity strategy を固定する。
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S4-01] conformance 結果の要約を support matrix / docs / tooling へ handoff するルールを定める。

## S1-01 Feature-To-Fixture Seed

- seed export:
  - manifest: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()`
  - CLI/export seam: [export_backend_feature_contract_manifest.py](/workspace/Pytra/tools/gen/export_backend_feature_contract_manifest.py)
- mapping rule:
  - 各 `feature_id` は representative fixture path を 1 つだけ持つ。
  - 複数 feature が同じ fixture を共有してよいが、その共有は `fixture_mapping[*].shared_fixture_feature_ids` で明示する。
  - fixture category は `feature_id` の category とは別に `fixture_scope` (`syntax_case` / `builtin_case` / `stdlib_case`) で固定する。
- fixture bucket taxonomy:
  - `syntax_case`: `core`, `collections`, `control`, `oop`
  - `builtin_case`: `core`, `control`, `oop`, `signature`, `strings`, `typing`
  - `stdlib_case`: `stdlib`
- representative rule:
  - `stdlib.*` feature は必ず `test/fixtures/stdlib/*.py` を representative fixture に使う。
  - `syntax.*` と `builtin.*` は同一 fixture の共有を許すが、共有は manifest export で追跡する。

## S2-01 Shared Harness Lane Contract

- source of truth:
  - lane contract: [backend_conformance_harness_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_harness_contract.py)
  - runner seed manifest: [backend_conformance_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_inventory.py)
  - CLI/export seam: [export_backend_conformance_seed_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_seed_manifest.py)
  - validation: [check_backend_conformance_harness_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_harness_contract.py), [test_check_backend_conformance_harness_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_harness_contract.py)
- stage order:
  - `frontend`: `parse`
  - `ir`: `east`, `east3_lowering`
  - `backend`: `emit`
  - `runtime`: `runtime`
- backend selection rule:
  - `parse/east/east3_lowering` は backend 非依存 lane として固定する。
  - `emit/runtime` は backend-selectable lane として固定し、representative backend order は `cpp -> rs -> cs` を seed にする。
- result contract:
  - `parse`: `parse_result` / `parser_success_or_frontend_diagnostic`
  - `east`: `east_document` / `east_document_or_frontend_diagnostic`
  - `east3_lowering`: `east3_document` / `east3_document_or_lowering_diagnostic`
  - `emit`: `module_artifact` / `artifact_or_fail_closed_backend_diagnostic`
  - `runtime`: `runtime_execution` / `stdout_stderr_exit_or_fail_closed_backend_diagnostic`
- fixture binding rule:
  - representative fixture class order は `syntax`, `builtin`, `pytra_std` で固定する。
  - すべての lane は同じ representative fixture inventory を共有し、lane ごとに別 vocabulary を持ち込まない。
- runner seed manifest は `lane_harness` と `fixture_lane_policy` を含み、`S2-02` runner はそこから CLI / compare-unit / runtime strategy を読む。

## S2-02 Backend-Selectable Runner Seed

- source of truth:
  - runner contract: [backend_conformance_runner_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_runner_contract.py)
  - CLI/export seam: [export_backend_conformance_runner_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_runner_manifest.py)
  - validation: [check_backend_conformance_runner_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_runner_contract.py), [test_check_backend_conformance_runner_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_runner_contract.py)
- representative backend order:
  - `cpp -> rs -> cs`
- backend-selectable lane rule:
  - runner が backend を切り替える lane は `emit/runtime` に固定する。
  - `parse/east/east3_lowering` は `S2-01` の shared harness contract 側に留め、runner inventory に別 vocabulary を持ち込まない。
- entrypoint rule:
  - `emit`: `src/pytra-cli.py`
  - `runtime`: `tools/check/runtime_parity_check.py`
- smoke binding rule:
  - `cpp`: `tools/unittest/emit/cpp/test_py2cpp_features.py`
  - `rs`: `tools/unittest/emit/rs/test_py2rs_smoke.py`
  - `cs`: `tools/unittest/emit/cs/test_py2cs_smoke.py`
- handoff rule:
  - runner manifest は backend order / selectable lanes / lane entrypoints / smoke binding を固定し、`S3-01` の stdlib runtime parity strategy と `S4-01` の summary handoff はこの manifest だけを見る。

## S3-01 Stdlib Runtime Parity Strategy

- source of truth:
  - runtime strategy contract: [backend_conformance_runtime_parity_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_runtime_parity_contract.py)
  - CLI/export seam: [export_backend_conformance_runtime_parity_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_runtime_parity_manifest.py)
  - validation: [check_backend_conformance_runtime_parity_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_runtime_parity_contract.py), [test_check_backend_conformance_runtime_parity_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_runtime_parity_contract.py)
- representative module order:
  - `json`, `pathlib`, `enum`, `argparse`, `math`, `re`
- runtime strategy rule:
  - `fixture_class=pytra_std` の runtime lane はすべて `stdlib_module_runtime_case` に固定する。
  - case root は `fixture`、runner lane は `runtime`、entrypoint は `tools/check/runtime_parity_check.py` に固定する。
  - compare unit は `normalized_stdout_exitcode_artifact_digest` を使い、backend order は `cpp -> rs -> cs` を使う。
- fixture binding rule:
  - `json`: `test/fixtures/stdlib/json_extended.py`
  - `pathlib`: `test/fixtures/stdlib/pathlib_extended.py`
  - `enum`: `test/fixtures/stdlib/enum_extended.py`
  - `argparse`: `test/fixtures/stdlib/argparse_extended.py`
  - `math`: `test/fixtures/stdlib/pytra_std_import_math.py`
  - `re`: `test/fixtures/stdlib/re_extended.py`
- handoff rule:
  - `S4-01` の support matrix/docs/tooling handoff は stdlib runtime lane の representative module list と compare unit をこの manifest から読む。

## S4-01 Conformance Summary Handoff

- source of truth:
  - summary handoff contract: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
  - CLI/export seam: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_summary_handoff_manifest.py)
  - validation: [check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_summary_handoff_contract.py), [test_check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_summary_handoff_contract.py), [test_export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_conformance_summary_handoff_manifest.py)
- destination order:
  - `support_matrix -> docs -> tooling`
- required manifest rule:
  - `feature_matrix_seed`: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest`
  - `conformance_seed`: `backend_conformance_inventory.build_backend_conformance_seed_manifest`
  - `runner_seed`: `backend_conformance_runner_contract.build_backend_conformance_runner_manifest`
  - `stdlib_runtime_seed`: `backend_conformance_runtime_parity_contract.build_backend_conformance_runtime_parity_manifest`
- summary handoff rule:
  - `support_matrix` は `feature_id/category/representative_fixture/backend_order/support_state_order` を handoff する。
  - `docs` は `module_name/case_stem/compare_unit/representative_backends` を handoff する。
  - `tooling` は `lane_order/lane_harness/fixture_lane_policy/backend_order/selectable_lanes` を handoff する。
- downstream rule:
  - handoff の downstream task / plan は `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` と `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md` に固定する。

## 決定ログ

- 2026-03-12: conformance suite は `P5` の feature contract の次段として扱い、基準未整備のまま先に matrix 化しないため `P6` に置く。
- 2026-03-12: 既存 smoke test を即時に捨てるのではなく、representative lane から共通 harness を段階導入する。
- 2026-03-12: `P6` は `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["conformance_handoff"]` を representative fixture/lane/backend-order の seed として使う。
- 2026-03-12: `S1-01` では `fixture_mapping` / `fixture_scope_order` / `fixture_bucket_order` を manifest に追加し、feature-to-fixture 共有規則を `build_feature_contract_handoff_manifest()` と CLI export seam に固定した。
- 2026-03-12: `S2-01` では `parse/east/east3_lowering` を backend 非依存 lane、`emit/runtime` を backend-selectable lane とする shared harness contract を `backend_conformance_harness_contract.py` に固定した。
- 2026-03-12: `S2-01` では `backend_conformance_inventory.build_backend_conformance_seed_manifest()` と `export_backend_conformance_seed_manifest.py` も追加し、runner seed の `lane_harness` / `fixture_lane_policy` を固定した。
- 2026-03-12: `S2-02` では `backend_conformance_runner_contract.py` と `export_backend_conformance_runner_manifest.py` を追加し、representative backend order を `cpp -> rs -> cs`、backend-selectable lane を `emit/runtime`、per-backend smoke binding を runner manifest に固定した。
- 2026-03-12: `S3-01` では `backend_conformance_runtime_parity_contract.py` と `export_backend_conformance_runtime_parity_manifest.py` を追加し、`pytra_std` runtime lane を `stdlib_module_runtime_case` として `json/pathlib/enum/argparse/math/re` へ固定した。
- 2026-03-12: `S4-01` では `backend_conformance_summary_handoff_contract.py` と `export_backend_conformance_summary_handoff_manifest.py` を正本にし、support matrix/docs/tooling への downstream handoff を `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` 向けに固定した。
