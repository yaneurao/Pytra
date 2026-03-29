<a href="../../../en/plans/archive/20260312-p0-relative-import-diagnostic-realign.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: relative import 診断契約の再整列

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01`

背景:
- relative import 自体は current frontend / import graph で実装済みで、sibling / parent package / `from . import helper` は通る。
- その一方で frontend 診断面には stale な `relative import is not supported` / `kind=unsupported_import_form` が残っている。
- 現状のままだと、supported relative import と fail-closed すべき root escape / invalid relative import が同じ診断 bucket に見え、ユーザーから見ると「相対 import 全体が未対応」に見える。
- 特に `Pytra-NES` のような package-relative import を多用する実験では、この stale 診断が心理的にも実務的にも blocker になる。

目的:
- supported relative import と fail-closed relative import を診断上で明確に分離する。
- `unsupported_import_form` の blanket 使用をやめ、relative import root escape / invalid relative import 専用の current contract を定める。
- CLI / import graph / backend smoke の representative regression を current support state に揃える。

対象:
- `transpile_cli.py` の import diagnostics helper
- import graph validation / report の relative import issue kind
- import diagnostics / import graph structure / CLI / backend smoke test
- TODO / plan / English mirror

非対象:
- relative import 自体の新規機能追加
- wildcard import / duplicate binding / cycle 検出アルゴリズムの再設計
- parser / import graph 全体の carrier 名大改名
- `core_stmt_parser.py` / `core_module_parser.py` の import 構文受理拡張

受け入れ基準:
- supported relative import を通す current test は維持されること。
- root escape など fail-closed relative import の診断が `unsupported_import_form` ではなく relative import 専用 kind で出ること。
- `transpile_cli._classify_import_user_error()` と `validate_import_graph_or_raise()` が同じ relative import diagnostic contract を使うこと。
- representative unit / CLI / backend regression が current contract で固定されること。
- `docs/ja/todo/index.md` の進捗は 1 行要約に留め、詳細はこの plan の決定ログへ残すこと。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 tools/unittest/tooling/test_py2x_cli.py -k relative_import -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: relative import 実装そのものではなく、stale diagnostics を是正する task として `P0` 起票した。priority は user blocker 性を考慮して `P0` に置く。
- 2026-03-12: `S2-01` では carrier 名 (`relative_import_entries`) は触らず、まず user-facing diagnostic kind を `relative_import_escape` へ切り替える。内部 field rename は後続 slice へ送る。
- 2026-03-12: `S2-02` では structured import envelope の canonical code/message も `relative_import_escape` に揃える。legacy `unsupported_import_form: relative import is not supported` は fallback 互換だけ残す。
- 2026-03-12: frontend helper / import graph validation / focused common test はすでに `relative_import_escape` へ揃っていた。残差分は spec の stale `unsupported_import_form` 記述と TODO/plan 上の未完了表示だったため、`S2-01` と `S2-02` は contract sync と focused regression 再確認で閉じる。
- 2026-03-12: `S3-01` は spec / TODO / plan の wording cleanup に限定し、relative import 機能追加は含めない。archive-ready 条件は CLI / import graph / backend smoke / spec が `relative_import_escape` で一貫することとした。

## 分解

- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S1-01] current stale diagnostics / desired contract / representative failing surfaces を plan と TODO に固定する。
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S2-01] relative import root escape を専用 diagnostic kind へ切り替え、frontend helper / import graph validation / focused test を揃える。
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S2-02] CLI / backend smoke / import graph structure test を current contract へ追従させる。
- [x] [ID: P0-RELATIVE-IMPORT-DIAGNOSTIC-REALIGN-01-S3-01] residual stale wording を掃除し、archive 可能な end state を plan に固定する。
