<a href="../../en/plans/p2-swap-name-only-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: Swap ノードを Name 限定に制約し、Subscript swap を Assign 展開する

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-SWAP-NAME-ONLY-01`

## 背景

- EAST3 の Swap ノードは `left`/`right` に任意の式（Name / Subscript / Attribute）を許容している。
- Subscript swap（`values[i], values[j] = values[j], values[i]`）の場合、各 emitter が個別に「読み取り」と「書き込み」を分けて処理する必要がある。
- Go / Swift / Java / C# 等が同じ分岐ロジックを各自で実装しており、保守性が低い。
- Name-only の swap なら、言語固有の swap 構文（Go の多重代入、Rust の `std::mem::swap`、C++ の `std::swap`）をそのまま活かせる。

## 目的

- Swap ノードの契約を「left/right が共に Name」に限定する。
- Subscript を含む swap パターンは、EAST3 lowering で一時変数付き Assign 列に展開する。
- 全 emitter から Subscript swap の分岐を除去可能にする。

## 非対象

- 各 emitter の Subscript 分岐除去（本タスクは EAST3 側のみ。emitter 側は各 backend が自主的に除去）。

## 受け入れ基準

1. Name-Name swap → 従来通り Swap ノードを生成。
2. Subscript を含む swap → 一時変数付き Assign 列を生成（Swap ノードにならない）。
3. `sample/py/12_sort_visualizer.py` の Subscript swap が正しく展開される。
4. 既存テストに回帰がない。

## 決定ログ

- 2026-03-23: Go 担当からの Swap `target_kinds` 提案を「冗長」として却下。Subscript swap を EAST3 lowering で展開する方式を採用。
- 2026-03-23: S1-S2 完了。`east2_to_east3_swap_detection.py` を修正し、Name-Name swap のみ Swap ノード、Subscript 含む swap は `__swap_tmp_N` を使った 3 文の Assign 列に展開。`tools/unittest/ir/test_east3_swap_detection.py` に 7 テスト追加（Name swap、Subscript swap、BinOp index swap、mixed swap、非 swap、複数 swap の一意 tmp 名）。
