<a href="../../../en/plans/archive/20260311-p1-import-graph-request-carriers.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: import graph の request carrier を構造化する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/archive/20260311.md` の `ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01`

背景:
- 現在の import graph は `collect_import_modules()` が返す string list を前提にしており、`Import` と `ImportFrom` の違い、`symbol` 名、dot-only relative import の submodule 候補が早い段階で失われる。
- `from . import helper` を通す修正でも、`"."` を `".helper"` へ flatten する特殊処理を `collect_import_modules()` に入れる必要があった。
- 今後 `from . import a, b`、package export / submodule の切り分け、graph diagnostics の精密化を進めるには、string flatten の前に structured carrier を持つ必要がある。

目的:
- import graph が扱う import 情報を `kind/module/symbol` を持つ structured request carrier に揃え、string flatten は compatibility helper へ後退させる。
- まず helper と focused regression を整え、その後 graph 本体を bundle 単位で carrier-first に寄せる。

対象:
- `collect_import_requests()` の導入
- `collect_import_modules()` の compatibility helper 化
- `from . import helper` representative regression の structured carrier 固定
- TODO / plan / English mirror の整合

非対象:
- relative import の新仕様追加
- import graph 全体の一括書き換え
- package export / submodule ambiguity の完全解決

受け入れ基準:
- `collect_import_requests()` が `Import` / `ImportFrom` の `kind/module/symbol` を保持すること。
- `collect_import_modules()` は structured carrier の compatibility wrapper として動作し、既存 smoke を壊さないこと。
- `from . import helper` の regression が unit / CLI smoke で通ること。
- `python3 tools/check_todo_priority.py`、対象 unit test、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-11: `from . import helper` を通す際、graph helper が string module list しか見ていないことが残 cluster だと分かった。follow-up は import graph を即全面改修するのではなく、structured request helper を先に導入する段階的移行にする。
- 2026-03-11: `S2-02` として `analyze_import_graph()` と `east1_build._analyze_import_graph_impl()` を `collect_import_requests()` + `collect_import_request_modules()` の carrier-first loop に切り替え、`from . import helper` の representative graph regression を両 lane で固定した。
- 2026-03-11: graph lane と `east1_build` mirror の representative request-carrier 移行が完了したため、remaining work は docs / archive closeout のみと判断し、そのまま archive へ移した。

## 分解

- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S1-01] current string flatten gap と staged end state を plan/TODO に固定する。
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S2-01] `collect_import_requests()` と focused regression を追加し、`collect_import_modules()` を compatibility helper 化する。
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S2-02] import graph / east1_build の representative lane を request carrier-first に寄せる。
- [x] [ID: P1-IMPORT-GRAPH-REQUEST-CARRIERS-01-S3-01] docs / archive を更新して閉じる。
