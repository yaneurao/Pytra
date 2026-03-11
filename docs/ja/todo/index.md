# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-11

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### P1: `east2_to_east3_lowering.py` の残 cluster を第二波で分割する

文脈: [docs/ja/plans/p1-east23-lowering-orchestration-split.md](../plans/p1-east23-lowering-orchestration-split.md)

1. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01] `east2_to_east3_lowering.py` の残 cluster を dedicated module へ寄せ、main file を orchestration / dispatch 中心に整理する。
2. [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] 残 cluster を `call_metadata` / `stmt_lowering` / `dispatch_orchestration` に棚卸しし、split 順を固定する。
3. [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] 進捗メモは bundle 単位へ圧縮し、main file end state を `dispatch + lifecycle` 中心に固定する。
4. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] `call metadata` / `json decode fastpath` cluster を dedicated module へ分割する。
5. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] `Assign` / `For` / `ForRange` lowering cluster を dedicated module へ分割する。
6. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] `Attribute` / `Match` / `ForCore` loweringと node dispatch orchestration を dedicated module へ分割する。
7. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] source-contract と representative regression を second-wave split layout へ追従させる。
8. [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] docs / TODO / archive を更新して閉じる。
- 進捗メモ: [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] 残り 833 行の main file は `call metadata/json decode`, `stmt lowering`, `dispatch/orchestration` の 3 cluster に整理され、第二波 split の順を固定した。
