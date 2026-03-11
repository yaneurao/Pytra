# P7 Backend Parity Rollout And Matrix

最終更新: 2026-03-12

目的:
- backend parity の進捗を feature × backend で見える化し、どの backend が `supported` / `fail_closed` / `not_started` かを継続的に追えるようにする。
- 新 feature の merge 条件に parity 観点を組み込み、C++ 単独の completion 判定をやめる。
- support matrix と rollout 順を docs / tooling / review 運用へ定着させる。

背景:
- `P5` で contract、`P6` で conformance basis が整っても、日常運用に落とし込まないと C++ 優遇は再発する。
- `P5` の `support_matrix_handoff` と `support_state_order` を seed にしないと、matrix 側で別 vocabulary を持ち込みやすい。
- 現在の support 情報は backend 別ページや個別 note に散っており、feature 横断での比較が弱い。
- merge/review 時に parity をチェックする手順が制度化されていないため、「C++ は通るが他 backend は未整理」という変更が入りやすい。
- したがって最後に、matrix・rollout 順・受け入れ条件・docs の定常運用を固定する必要がある。

非対象:
- すべての backend を同時に feature-complete にすること。
- backend ごとの個別最適化や性能 tuning。
- 既存 docs 構造の全面 rewrite。

受け入れ基準:
- feature × backend の support matrix をどの source から生成・保守するかが決まっている。
- rollout 順（例: representative backend から tier 拡張）が定義されている。
- 新 feature 導入時の review / merge checklist に parity 観点を入れる方針が決まっている。
- docs / support pages / tooling が matrix を参照する運用へ handoff される。
- `docs/en/` mirror が日本語版と同じ内容に追従している。

## 子タスク

- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S1-01] feature × backend support matrix の source of truth と publish 先を決める。
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-01] representative backend → secondary backend → long-tail backend の rollout tier と優先順を固定する。
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-02] 新 feature merge 時の parity review checklist と fail-closed requirement を定義する。
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S3-01] support matrix を docs / release note / tooling に handoff する手順を決める。
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S4-01] rollout policy と matrix maintenance の archive / operations rule を整える。

## 決定ログ

- 2026-03-12: parity の制度運用は contract と conformance の後でなければ空文化しやすいため `P7` に置く。
- 2026-03-12: backend parity は「全 backend を同時に実装する」ではなく、「support state を可視化し、未対応は fail-closed に保つ」方針で進める。
- 2026-03-12: `P7` は `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["support_matrix_handoff"]` と `support_state_order` を matrix row/state seed として使う。

## S1-01 Matrix Source Of Truth And Publish Path

- source of truth:
  - matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
  - row/state seed: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py) の `iter_representative_support_matrix_handoff()` / `SUPPORT_STATE_ORDER`
  - conformance summary seed contract: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
  - CLI/export seam: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py), [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/export_backend_conformance_summary_handoff_manifest.py)
  - validation: [check_backend_parity_matrix_contract.py](/workspace/Pytra/tools/check_backend_parity_matrix_contract.py), [test_check_backend_parity_matrix_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_matrix_contract.py), [check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/check_backend_conformance_summary_handoff_contract.py), [test_check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_conformance_summary_handoff_contract.py), [test_export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/test/unit/tooling/test_export_backend_conformance_summary_handoff_manifest.py)
- source manifest rule:
  - `feature_contract_seed`: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest`
  - `conformance_summary_seed`: `backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest`
  - matrix の canonical destination は `support_matrix` に固定する。
- row/source rule:
  - row seed は `iter_representative_support_matrix_handoff()` を使い、`feature_id/category/representative_fixture/backend_order/support_state_order` をそのまま row key にする。
  - summary seed は P6 の representative conformance summary handoff を使い、matrix 側では `representative_summary_entries` の allowlist key だけを読む。
- publish path rule:
  - 日本語 docs publish path は `docs/ja/language/backend-parity-matrix.md`
  - 英語 docs publish path は `docs/en/language/backend-parity-matrix.md`
  - tooling publish seam は `tools/export_backend_parity_matrix_manifest.py`
  - conformance summary handoff の publish target order は `support_matrix -> docs -> tooling` に固定する。
- downstream rule:
  - downstream task / plan は `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` と `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md` に固定する。

- 2026-03-12: `S1-01` では `backend_parity_matrix_contract.py` を正本にし、row/state seed を `backend_feature_contract_inventory.iter_representative_support_matrix_handoff()`、summary seed を `backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest()` に固定した。
