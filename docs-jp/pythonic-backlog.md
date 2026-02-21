# Pythonic Backlog（低優先）

最終更新: 2026-02-21

このメモは、selfhost 安定化のために平易化した実装を、将来的に一般的な Python 風記法へ戻す候補一覧です。  
`docs-jp/todo.md` の P3 タスクに対応します。

## src/py2cpp.py

- `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
- `text[0:1] == "x"` のような1文字比較を、selfhost 要件を満たす範囲で `text.startswith("x")` へ戻す。
- 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
- 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
- import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

## src/pytra/compiler/east_parts/code_emitter.py

- `split_*` / `normalize_type_name` 周辺の index ループを段階的に `for` ベースへ戻す。
- `any_*` 系ヘルパで重複する `None`/空文字判定を共通小関数へ集約する。
- `_emit_trivia_items` の directive 処理分岐を小関数に分割する。
- `hook_on_*` 系で同型の呼び出しパターンを汎用ヘルパ化し、重複を減らす。

## 進め方（運用ルール）

- 1パッチで戻す範囲は小さく保つ（1〜3関数）。
- 各パッチで必ず以下を実行する。
  - `python3 tools/check_py2cpp_transpile.py`
  - `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`
- 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。
