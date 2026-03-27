<a href="../../../en/plans/archive/20260311-p1-import-graph-issue-structure.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: import graph issue carrier の構造化

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/archive/20260311.md` の `ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01`

背景:
- import graph 解析は `relative_imports` / `missing_modules` / `cycles` などを `"<file>: <module>"` 形式の文字列 list で保持していた。
- frontend 側では [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) の `split_graph_issue_entry()` がその文字列を再分解しており、carrier と consumer が両方とも stringly-typed だった。
- `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01` で import diagnostic 自体は structured-first に寄せたため、次は import graph issue carrier も helper 境界へ寄せて brittle な `file: module` 再解釈を減らしたかった。

目的:
- import graph issue carrier を helper-structured seam に寄せ、`validate_import_graph_or_raise()` と report formatter の stringly 依存を減らす。
- current CLI detail / `--dump-deps` 表示契約は壊さず、graph analyzer と consumer の境界だけを整理する。

対象:
- import graph issue entry の helper 追加
- `relative_imports` / `missing_modules` / `cycles` / `reserved_conflicts` の representative carrier 正規化
- focused unit test と source-contract の追加
- TODO / plan / English mirror の整合

非対象:
- import graph アルゴリズム自体の変更
- relative import / missing module / cycle 判定ロジックの仕様変更
- import diagnostics 全般の再設計

受け入れ基準:
- graph issue entry を直接 `"<file>: <module>"` 連結・再分解する箇所が helper 経由に集約されること。
- `validate_import_graph_or_raise()` と `format_import_graph_report()` の current output contract が維持されること。
- focused unit test が helper を直接検証し、既存 CLI / report representative regression が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-11: `P1-IMPORT-DIAGNOSTIC-STRUCTURE-01` 完了後の次段として起票。v1 は raw string list を即 dict 化するのではなく、graph issue helper を導入して producer / consumer の文字列連結・分解を 1 箇所へ集約する。
- 2026-03-11: `make_graph_issue_entry()` / `normalize_graph_issue_entry()` / `format_graph_issue_entry()` と `dict_any_get_graph_issue_entries()` を canonical seam とし、producer は structured entry を保持しつつ legacy text list を互換 export する方針で固定した。
- 2026-03-11: `validate_import_graph_or_raise()` / `format_import_graph_report()` / `east1_build` mirror は structured entry を優先して読み、representative regression では stale legacy text より structured key を優先することを固定した。

## 完了した分解

- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S1-01] current import graph issue carrier と staged end state を棚卸しし、plan/TODO に固定する。
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-01] graph issue entry の shared helper と focused unit test を追加し、`split_graph_issue_entry()` / producer 側の直列 formatting を helper 経由へ集約する。
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S2-02] `validate_import_graph_or_raise()` / `format_import_graph_report()` / `east1_build` mirror を helper-structured seam に揃える。
- [x] [ID: P1-IMPORT-GRAPH-ISSUE-STRUCTURE-01-S3-01] representative CLI / report regression、docs、archive を更新して閉じる。

## 成果

- import graph issue carrier は `missing_module_entries` / `relative_import_entries` の structured-first seam を持ち、legacy `missing_modules` / `relative_imports` は compatibility export としてのみ残る。
- report formatter と validator は structured entry を優先し、既存の text contract を維持した。
- focused helper test、CLI relative import regression、representative report/validator regression を通して archive へ移した。
