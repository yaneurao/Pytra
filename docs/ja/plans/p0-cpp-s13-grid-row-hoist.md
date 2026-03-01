# P0: sample/13 `grid` 行アクセス hoist

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-GRID-ROW-HOIST-01`

背景:
- sample/13 では `grid[y][x]` / `grid[ny][nx]` 周辺で `py_at(grid, ... )` が同一ループ内で繰り返し評価される。
- 2 次元アクセスの行単位一時変数がないため、冗長な object アクセス列が増えている。

目的:
- 行アクセスを `row` 一時変数へ hoist し、同一インデックスの repeated `py_at(grid, y)` を削減する。

対象:
- `src/hooks/cpp/emitter/stmt.py` / `expr.py`（subscript 展開）
- 必要に応じて `src/hooks/cpp/optimizer/passes/*`
- `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- 全サンプル一括の CSE 最適化
- runtime の list/dict API 変更

受け入れ基準:
- sample/13 の `capture` / main loop で行アクセスが hoist される。
- `object(py_at(grid, ...))` の重複が減る。
- 回帰テストと transpile check が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー要望により、sample/13 の row hoist を独立 P0 として起票。
- 2026-03-01: concrete typed-list 拡張後の sample/13 では `grid` アクセスが `grid[y][x]` 直参照へ落ち、`py_at(grid, ...)` / `object(py_at(grid, ...))` が消えていたため、専用 hoist 実装は追加せず回帰テストで固定した。

## 分解

- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S1-01] row hoist 対象パターン（同一 index の `grid` 再参照）を定義する。
- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S2-01] emitter/optimizer に row hoist を実装し、sample/13 出力を縮退する。
- [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S3-01] 回帰を追加し、transpile/check を通す。
