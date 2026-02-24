# TASK GROUP: TG-P0-EAST1-BUILD-COMPAT-REMOVAL

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-EAST1-BUILD-01` 〜 `P0-EAST1-BUILD-01-S4`

背景:
- `import graph` 解析や `.py/.json -> EAST` build 入口は本来 `EAST1` 側責務だが、現状は `py2cpp.py` から `transpile_cli` の互換 helper を経由する運用が残っている。
- この互換運用により、責務境界が曖昧になり `py2cpp.py` 側の肥大化と保守負荷が継続している。
- ユーザー指示として「互換運用は不要、廃止する」が確定している。

目的:
- `EAST1 build`/`import graph` を `east_parts` 側の正規責務へ移し、`py2cpp.py` と `transpile_cli` に残る互換運用を廃止する。

対象:
- `src/py2cpp.py` の import graph 解析呼び出し境界（`_analyze_import_graph` など）。
- `src/pytra/compiler/transpile_cli.py` のうち、`py2cpp` 向け互換導線として残っている import graph / build helper。
- `src/pytra/compiler/east_parts/` への責務移管（`east1_build.py` 追加を含む）。

非対象:
- 他言語トランスパイラの即時全面移行。
- import graph 仕様そのものの変更。

受け入れ基準:
- `py2cpp.py` が import graph/build で互換 helper へ依存せず、`EAST1` 側の正規 API を利用する。
- `transpile_cli.py` の互換専用導線が撤去または最小化される。
- 責務境界（`EAST1 build` が担当する範囲）が `spec-east`/`spec-dev` に同期される。
- 既存の `check_py2cpp_transpile` / smoke / import graph 検証が通る。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest test.unit.test_py2cpp_smoke`
- `python3 tools/check_todo_priority.py`

決定ログ:
- 2026-02-24: ユーザー指示により、`py2cpp` 起点の `EAST1 build/import graph` 互換運用を廃止し、最優先群の2番目として着手する方針を確定。
