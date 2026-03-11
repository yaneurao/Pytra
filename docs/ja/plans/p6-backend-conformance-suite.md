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
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-02] C++ / Rust / C# を first representative lane とする backend-selectable conformance runner の方針を決める。
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S3-01] `pytra.std.*` representative module（例: `json`, `pathlib`, `enum`, `argparse`）の runtime parity strategy を固定する。
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S4-01] conformance 結果の要約を support matrix / docs / tooling へ handoff するルールを定める。

## S1-01 Feature-To-Fixture Seed

- seed export:
  - manifest: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()`
  - CLI/export seam: [export_backend_feature_contract_manifest.py](/workspace/Pytra/tools/export_backend_feature_contract_manifest.py)
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
  - validation: [check_backend_conformance_harness_contract.py](/workspace/Pytra/tools/check_backend_conformance_harness_contract.py), [test_check_backend_conformance_harness_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_conformance_harness_contract.py)
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

## 決定ログ

- 2026-03-12: conformance suite は `P5` の feature contract の次段として扱い、基準未整備のまま先に matrix 化しないため `P6` に置く。
- 2026-03-12: 既存 smoke test を即時に捨てるのではなく、representative lane から共通 harness を段階導入する。
- 2026-03-12: `P6` は `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["conformance_handoff"]` を representative fixture/lane/backend-order の seed として使う。
- 2026-03-12: `S1-01` では `fixture_mapping` / `fixture_scope_order` / `fixture_bucket_order` を manifest に追加し、feature-to-fixture 共有規則を `build_feature_contract_handoff_manifest()` と CLI export seam に固定した。
- 2026-03-12: `S2-01` では `parse/east/east3_lowering` を backend 非依存 lane、`emit/runtime` を backend-selectable lane とする shared harness contract を `backend_conformance_harness_contract.py` に固定した。
