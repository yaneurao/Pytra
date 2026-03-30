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

1. [ ] [ID: P0-CHANGELOG-S1] `runtime_parity_check_fast.py` で結果保存時に前回 PASS 件数と比較し、変化があれば `progress-preview/changelog.md` に行を追記する
2. [ ] [ID: P0-CHANGELOG-S2] `runtime_parity_check.py`（非 fast 版）にも同様のロジックを追加する
3. [ ] [ID: P0-CHANGELOG-S3] 動作確認 — parity check 実行後に changelog.md が正しく更新されることを確認する

### P20-EMIT-EXPECT: emitter テストのデータ駆動化

文脈: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

ステータス: **保留中** — 既存テストが他 agent により変更中のため、安定してから着手する。

1. [ ] [ID: P20-EMIT-EXPECT-S1] `test/fixture/emit-expect/<lang>/` に JSON テストケース形式を定義する
2. [ ] [ID: P20-EMIT-EXPECT-S2] pytest parametrize ベースの汎用テストランナーを1本作成する
3. [ ] [ID: P20-EMIT-EXPECT-S3] `test_common_renderer.py` の emitter 出力テストを段階的に JSON ケースへ移行する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
