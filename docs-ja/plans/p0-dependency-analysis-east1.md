# TASK GROUP: TG-P0-DEP-ANALYSIS-EAST1

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-DEP-EAST1-01` 〜 `P0-DEP-EAST1-01-S4`

背景:
- 依存解析（import graph 解析、モジュール解決、循環/欠落検出）は `EAST1 build` 層の責務であり、`py2cpp` 固有責務ではない。
- 現状は `py2cpp.py` と `transpile_cli.py` の互換導線に依存解析ロジックが残り、責務境界が曖昧になっている。
- ユーザー方針として「依存解析は `EAST1` 側責務へ統一する」が確定している。

目的:
- 依存解析を `east_parts/east1_build` へ集約し、`py2cpp.py` から切り離す。

対象:
- `src/pytra/compiler/east_parts/east1_build.py` の依存解析 API。
- `src/pytra/compiler/transpile_cli.py` にある import graph helper 群の移管または薄い委譲化。
- `src/py2cpp.py` の依存解析呼び出し境界。

非対象:
- 依存解析アルゴリズム自体の仕様変更（解決ルール変更など）。
- 他言語 CLI の即時全面置換。

着手前提:
- `P0-EAST1-BUILD-01`（`EAST1 build` 互換運用廃止）が完了済みであること。
- 上記完了は `docs-ja/todo/archive/20260224.md` の `P0-EAST1-BUILD-01` 移管セクションを正本として扱う。

受け入れ基準:
- `py2cpp.py` が依存解析実装詳細を持たず、`EAST1 build` API のみを呼ぶ。
- 依存解析本体は `east_parts` 側にあり、`transpile_cli.py` は互換薄層または非保持となる。
- 依存解析の責務境界を `spec-east` / `spec-dev` へ反映する。
- 既存の import graph 解析結果（循環・欠落・予約語衝突）に回帰がない。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest test.unit.test_py2cpp_smoke`
- `python3 tools/check_todo_priority.py`

決定ログ:
- 2026-02-24: ユーザー指示により、依存解析の責務を `EAST1 build` へ明示移管するタスクを `P0` 優先で追加。
- 2026-02-24: [ID: `P0-DEP-EAST1-01-S1`] P0-EAST1-BUILD-01 完了（archive 移管済み）を着手前提に固定し、`P0-DEP-EAST1-01` はこの前提を満たした状態で `S2` 以降を進める方針を確定。
- 2026-02-24: [ID: `P0-DEP-EAST1-01-S2`] import graph 解析本体を `east1_build` 側（`_analyze_import_graph_impl`）へ移し、`transpile_cli` の `analyze_import_graph` / `build_module_east_map` 公開名は `east1_build` thin wrapper へ固定した。
- 2026-02-24: [ID: `P0-DEP-EAST1-01-S3`] `py2cpp.py` の依存解析導線（`_analyze_import_graph`, `build_module_east_map`）が `East1BuildHelpers` 公開 API 呼び出しに収束していることを確認し、`transpile_cli` 実装詳細への直接参照を撤去済みと判断した。
