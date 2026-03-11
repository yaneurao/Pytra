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
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-01] representative backend → secondary backend → long-tail backend の rollout tier と優先順を固定する。
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-02] 新 feature merge 時の parity review checklist と fail-closed requirement を定義する。
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S3-01] support matrix を docs / release note / tooling に handoff する手順を決める。
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S4-01] rollout policy と matrix maintenance の archive / operations rule を整える。

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

## S2-01 Rollout Tier And Ordering

- source of truth:
  - rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
  - validation: [check_backend_parity_rollout_tier_contract.py](/workspace/Pytra/tools/check_backend_parity_rollout_tier_contract.py), [test_check_backend_parity_rollout_tier_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_rollout_tier_contract.py)
  - export seam: [export_backend_parity_rollout_tier_manifest.py](/workspace/Pytra/tools/export_backend_parity_rollout_tier_manifest.py), [test_export_backend_parity_rollout_tier_manifest.py](/workspace/Pytra/test/unit/tooling/test_export_backend_parity_rollout_tier_manifest.py)
- tier rule:
  - `representative`: `cpp -> rs -> cs`
  - `secondary`: `go -> java -> kt -> scala -> swift -> nim`
  - `long_tail`: `js -> ts -> lua -> rb -> php`
- ordering rule:
  - tier を連結した backend 順は `backend_feature_contract_inventory.SUPPORT_MATRIX_BACKEND_ORDER` と一致させる。
  - tier 間の backend 重複は禁止する。
- downstream rule:
  - downstream task / plan は `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` と `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md` に固定する。

- 2026-03-12: `S2-01` では rollout tier を `representative -> secondary -> long_tail` に固定し、連結順が support matrix backend order と一致することを contract/tooling で固定した。

## S2-02 Parity Review Checklist And Fail-Closed Requirement

- source of truth:
  - review checklist contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
  - validation: [check_backend_parity_review_contract.py](/workspace/Pytra/tools/check_backend_parity_review_contract.py), [test_check_backend_parity_review_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_review_contract.py)
  - export seam: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/export_backend_parity_review_manifest.py), [test_export_backend_parity_review_manifest.py](/workspace/Pytra/test/unit/tooling/test_export_backend_parity_review_manifest.py)
- checklist rule:
  - review checklist order は `feature_inventory -> matrix_state_recorded -> representative_tier_recorded -> later_tier_state_recorded -> unsupported_lanes_fail_closed -> docs_mirror` に固定する。
  - `feature_inventory` と `unsupported_lanes_fail_closed` は `backend_feature_contract_inventory.NEW_FEATURE_ACCEPTANCE_RULES` を seed にする。
  - `representative_tier_recorded` と `later_tier_state_recorded` は `backend_parity_rollout_tier_contract` の tier 順を seed にする。
- fail-closed rule:
  - `supported` 以外の lane は `fail_closed / not_started / experimental` のいずれかに固定し、silent fallback label は `object_fallback / string_fallback / comment_stub_fallback / empty_output_fallback` を禁止する。
  - phase rule は `parse_and_ir / emit_and_runtime / preview_rollout` を `backend_feature_contract_inventory.FAIL_CLOSED_PHASE_RULES` と一致させる。

- 2026-03-12: `S2-02` では parity review checklist を fixed order 化し、unsupported lane は `fail_closed/not_started/experimental` のいずれかで silent fallback を禁止する contract を追加した。

## S3-01 Docs / Release Note / Tooling Handoff

- source of truth:
  - handoff contract: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)
  - validation: [check_backend_parity_handoff_contract.py](/workspace/Pytra/tools/check_backend_parity_handoff_contract.py), [test_check_backend_parity_handoff_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_handoff_contract.py)
  - export seam: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/export_backend_parity_handoff_manifest.py), [test_export_backend_parity_handoff_manifest.py](/workspace/Pytra/test/unit/tooling/test_export_backend_parity_handoff_manifest.py)
- docs handoff rule:
  - matrix publish target は `docs/ja|en/language/backend-parity-matrix.md`
  - docs entrypoint は `docs/ja|en/index.md` と `docs/ja|en/language/index.md`
  - docs 側は support claim の正本ではなく、tooling manifest への publish target として扱う
- release note rule:
  - release note target は `docs/ja/README.md`, `README.md`, `docs/ja/news/index.md`, `docs/en/news/index.md`
  - release note は parity change の要約と matrix page へのリンクだけを持ち、backend ごとの support table を複製しない
- tooling rule:
  - tooling publish target は `export_backend_parity_matrix_manifest.py`, `export_backend_conformance_summary_handoff_manifest.py`, `export_backend_parity_review_manifest.py`, `export_backend_parity_handoff_manifest.py`
  - handoff manifest は matrix / conformance summary / review checklist / rollout tier の vocabulary をそのまま使う

- 2026-03-12: `S3-01` では docs / release note / tooling handoff を `backend_parity_handoff_contract.py` に固定し、matrix page と docs entrypoint を publish target に追加した。

## S4-01 Archive / Operations Rule

- source of truth:
  - operations contract: [backend_parity_operations_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_operations_contract.py)
  - validation: [check_backend_parity_operations_contract.py](/workspace/Pytra/tools/check_backend_parity_operations_contract.py), [test_check_backend_parity_operations_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_operations_contract.py)
  - export seam: [export_backend_parity_operations_manifest.py](/workspace/Pytra/tools/export_backend_parity_operations_manifest.py), [test_export_backend_parity_operations_manifest.py](/workspace/Pytra/test/unit/tooling/test_export_backend_parity_operations_manifest.py)
- operations rule:
  - maintenance order は `contract_seed -> docs_publish -> docs_entrypoints -> release_note_link -> tooling_export -> archive_handoff`
  - docs / README / news の parity matrix link は checker で固定し、publish target drift を fail-closed にする
  - tooling export は `export_backend_parity_matrix_manifest.py` と `export_backend_parity_handoff_manifest.py` を基準にする
- archive handoff rule:
  - `P7` 完了時は `docs/ja|en/todo/archive/index.md` と `docs/ja|en/plans/archive/` への handoff を同日で行う
  - archive handoff 後も live file として残すのは matrix page と parity contract 群

- 2026-03-12: `S4-01` では parity matrix maintenance order と archive handoff target を `backend_parity_operations_contract.py` に固定し、README / news / docs index の matrix link まで checker で監視するようにした。
