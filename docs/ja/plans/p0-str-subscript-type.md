<a href="../../en/plans/p0-str-subscript-type.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: str 型サブスクリプトの結果型推論

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-STR-SUBSCRIPT-TYPE`

## 背景

`s[i]` で `s: str` の場合、結果型は `str`（Python の意味論）。しかし EAST3 では `Subscript` ノードの `resolved_type` が `unknown` のまま。emitter が正しい型でコード生成できない。

## 対象

- EAST1 パーサーまたは EAST3 type propagation パスで、`str` 型の `Subscript` 結果を `str` に設定

## 子タスク

- [ ] [ID: P0-STR-SUBSCRIPT-TYPE-01] str 型サブスクリプトの結果型を `str` に推論する
- [ ] [ID: P0-STR-SUBSCRIPT-TYPE-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が `s[i]` の型が unknown になる問題を報告。
