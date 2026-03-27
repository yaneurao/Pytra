<a href="../../en/plans/p0-truediv-operator-lowering.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: __truediv__ 演算子の lowering（Path / "child" 等）

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TRUEDIV-LOWERING`

## 背景

Python の `Path("foo") / "bar"` は `Path.__truediv__(self, "bar")` を呼ぶ演算子オーバーロード。EAST3 では `BinOp(Div)` として表現されるが、emitter は `Path` 型の `/` 演算子を知らないため、数値除算として生成してしまう。

EAST3 lowering で、owner が `Path` 等の `__truediv__` を持つ型の場合に `BinOp(Div)` → メソッド呼び出しに変換すべき。

## 対象

- EAST3 lowering または type propagation パス

## 子タスク

- [ ] [ID: P0-TRUEDIV-LOWERING-01] `Path / "child"` を `Path.__truediv__` メソッド呼び出しに lowering する
- [ ] [ID: P0-TRUEDIV-LOWERING-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が `pathlib_extended` の `Path / "child"` が正しく変換されない問題を報告。
