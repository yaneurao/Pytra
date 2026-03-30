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

### P20-EMIT-EXPECT: emitter テストのデータ駆動化

文脈: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

ステータス: **保留中** — 既存テストが他 agent により変更中のため、安定してから着手する。

1. [ ] [ID: P20-EMIT-EXPECT-S1] `test/fixture/emit-expect/<lang>/` に JSON テストケース形式を定義する
2. [ ] [ID: P20-EMIT-EXPECT-S2] pytest parametrize ベースの汎用テストランナーを1本作成する
3. [ ] [ID: P20-EMIT-EXPECT-S3] `test_common_renderer.py` の emitter 出力テストを段階的に JSON ケースへ移行する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
