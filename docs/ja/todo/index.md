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

1. [ ] [ID: P1-IR-CORE-DECOMPOSITION-01] `core.py` / `test_east_core.py` を cluster 単位で分割し、source-contract と parser behavior の責務境界を整理する。
   文脈: [docs/ja/plans/p1-ir-core-decomposition.md](../plans/p1-ir-core-decomposition.md)
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S1-01] `core.py=10081 lines`、`test_east_core.py=3912 lines` を基準に、source-contract / parser behavior / suffix-call cluster の split boundary と bundle 粒度を固定した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S1-02] TODO には cluster 単位の一行進捗のみを残し、詳細ログは plan の `決定ログ` へ集約する運用に固定した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-01] shared support module と `test_east_core_source_contract_builders.py` を追加し、builder source-contract guard 10 本を `test_east_core.py` から切り出した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-02] source-contract guard 51 本を `test_east_core_source_contract_*.py` 5 file と既存 builders/expr-suffix file へ切り出し、`test_east_core.py` を parser behavior / representative regression 中心へ整理した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] `test_east_core_parser_behavior_decorators.py` を追加し、extern / abi / template の representative parser behavior 10 本を `test_east_core.py` から切り出した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] `test_east_core_parser_behavior_types.py` を追加し、decode-first / type-expr / typing future import の representative parser behavior 10 本を `test_east_core.py` から切り出した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] decorator/abi/template の負例 7 本と object receiver diagnostics 3 本を `test_east_core_parser_behavior_decorators.py` / `test_east_core_parser_behavior_diagnostics.py` へ切り出し、`test_east_core.py` 先頭の重複 test と stray assert を除去した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] `test_east_core_parser_behavior_exprs.py` を追加し、comprehension / lambda / fstring / yield / basic parser acceptance の representative 10 本を `test_east_core.py` から切り出した。
- 進捗メモ: [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] `test_east_core_parser_behavior_classes.py` を追加し、class storage hint / dataclass / nominal ADT / enum の representative parser behavior 7 本を `test_east_core.py` から切り出した。

1. [ ] [ID: P2-EAST-CORE-MODULARIZATION-01] [p2-east-core-modularization.md](../plans/p2-east-core-modularization.md) `core.py` / `test_east_core.py` を機能単位で分割し、cluster 単位で compiler 内部改良を進められる状態へ戻す。
