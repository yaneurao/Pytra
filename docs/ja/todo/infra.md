<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-31

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260330.md) を参照。

## 未完了タスク

### P0-PARITY-CHANGELOG: parity 変化点ログの自動記録

文脈: [docs/ja/plans/plan-parity-changelog.md](../plans/plan-parity-changelog.md)

parity check の PASS 件数が変化したタイミングで `progress-preview/changelog.md` に自動追記する。退行の即時検知と履歴追跡が目的。

1. [x] [ID: P0-CHANGELOG-S1] `runtime_parity_check_fast.py` で結果保存時に前回 PASS 件数と比較し、変化があれば `progress-preview/changelog.md` に行を追記する — `_save_parity_results` は fast 版が import して使うため、非 fast 版に実装することで両方に適用
2. [x] [ID: P0-CHANGELOG-S2] `runtime_parity_check.py`（非 fast 版）にも同様のロジックを追加する — `_save_parity_results` 内に `prev_pass`/`curr_pass` 計算と `_append_parity_changelog` 呼び出しを追加
3. [x] [ID: P0-CHANGELOG-S3] 動作確認 — parity check 実行後に changelog.md が正しく更新されることを確認する — ユニットテストで新規作成・行挿入・変化なし時スキップを確認

### P20-DATA-DRIVEN-TESTS: unittest のデータ駆動化

文脈: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

ステータス: **保留中** — 既存テストが他 agent により変更中のため、安定してから Phase 1 に着手する。

`tools/unittest/` の 269 スクリプトの大半は「入力 → パイプライン → 期待出力」のペアであり、JSON データで定義できる。テストランナーは 2 本（パイプライン用 + emit 用）だけにし、ケース追加は JSON ファイルを置くだけにする。

**Phase 1: emit 層で方式を確立**

1. [ ] [ID: P20-DDT-S1] `test/cases/emit/cpp/` に JSON テストケース 5〜10 件を作成する
2. [ ] [ID: P20-DDT-S2] `tools/unittest/test_emit_cases.py` を実装する（pytest parametrize で JSON 走査）
3. [ ] [ID: P20-DDT-S3] `test_common_renderer.py` の対応テストを JSON に移行し、元メソッドを削除する

**Phase 2: パイプライン層に横展開**

4. [ ] [ID: P20-DDT-S4] `test/cases/{east1,east2,east3}/` に JSON テストケースを作成する
5. [ ] [ID: P20-DDT-S5] `tools/unittest/test_pipeline_cases.py` を実装する
6. [ ] [ID: P20-DDT-S6] `tools/unittest/toolchain2/` の対応テストを段階的に JSON に移行する

**Phase 3: 既存スクリプトの縮退**

7. [ ] [ID: P20-DDT-S7] JSON に移行済みのテストメソッドを削除し、空になったスクリプトを削除する
8. [ ] [ID: P20-DDT-S8] `tools/unittest/emit/<lang>/` の言語別スクリプトを段階的に JSON に移行する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
