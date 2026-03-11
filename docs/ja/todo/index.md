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

### P1: 大型 expr split module を cluster 単位で分割する

文脈: [docs/ja/plans/p1-ir-expr-module-decomposition.md](../plans/p1-ir-expr-module-decomposition.md)

1. [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01] `toolchain/ir` の大型 expr split module を cluster 単位で分割し、`attr/subscript/call` の責務境界を明確にする。
2. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-01] `core_expr_attr_subscript_suffix.py` は `attr_suffix` / `subscript_suffix` / `shared_postfix_orchestration`、`core_expr_call_annotation.py` は `named_call` / `attr_call` / `callee_call` / `shared_state_orchestration` に分ける方針を固定した。
3. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S1-02] この task の進捗メモは bundle 単位の 1 行要約に圧縮し、helper 単位の列挙は plan 側へ寄せる運用に固定した。
4. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-01] `attr suffix` / `subscript suffix` cluster を [core_expr_attr_suffix.py](../../src/toolchain/ir/core_expr_attr_suffix.py) / [core_expr_subscript_suffix.py](../../src/toolchain/ir/core_expr_subscript_suffix.py) へ分割し、[core_expr_attr_subscript_suffix.py](../../src/toolchain/ir/core_expr_attr_subscript_suffix.py) は postfix facade に縮めた。
5. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S2-02] `named-call` / `attr-call` / `callee-call` annotation cluster を [core_expr_named_call_annotation.py](../../src/toolchain/ir/core_expr_named_call_annotation.py) / [core_expr_attr_call_annotation.py](../../src/toolchain/ir/core_expr_attr_call_annotation.py) / [core_expr_callee_call_annotation.py](../../src/toolchain/ir/core_expr_callee_call_annotation.py) へ分割し、[core_expr_call_annotation.py](../../src/toolchain/ir/core_expr_call_annotation.py) は shared call orchestration facade に縮めた。
6. [x] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S3-01] source-contract test を split 後の module 構成へ追従させ、representative regression を通した。
7. [ ] [ID: P1-IR-EXPR-MODULE-DECOMPOSITION-01-S4-01] docs / TODO / archive を更新し、完了 task を archive へ移す。
