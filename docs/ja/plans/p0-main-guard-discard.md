<a href="../../en/plans/p0-main-guard-discard.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: main_guard_body の Expr Call 戻り値を Discard ノードでラップ

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MAIN-GUARD-DISCARD`

## 背景

`main_guard_body`（`if __name__ == "__main__":` ブロック）内の `Expr Call` で呼ばれた関数が値を return すると、PowerShell/Ruby 等の動的言語で stdout に戻り値が漏れる。

Python では `Expr` 文の戻り値は捨てられるが、一部の言語では関数呼び出しの戻り値が暗黙的に出力される。

## 設計

linker の post-link pass または EAST3 lowering で、`main_guard_body` 内の `Expr` ノードの `value`（Call）に `Discard` ラッパーを追加する。emitter は `Discard` を見たら戻り値を明示的に捨てるコードを生成する。

## 子タスク

- [ ] [ID: P0-MAIN-GUARD-DISCARD-01] main_guard_body 内の Expr Call を Discard でラップする
- [ ] [ID: P0-MAIN-GUARD-DISCARD-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が main_guard_body の戻り値が stdout に漏れる問題を報告。全動的言語 backend に恩恵。
