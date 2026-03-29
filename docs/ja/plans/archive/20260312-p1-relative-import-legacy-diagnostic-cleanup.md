<a href="../../../en/plans/archive/20260312-p1-relative-import-legacy-diagnostic-cleanup.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: Relative Import Legacy Diagnostic Cleanup

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01`

背景:
- relative import の current contract はすでに `relative_import_escape` を canonical diagnostic kind として運用している。
- 一方で [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) には、旧 `unsupported_import_form: relative import is not supported` wording を `relative_import_escape` へ読み替える fallback がまだ残っていた。
- live source 上で `unsupported_import_form` を relative import 用に emit する producer は実質なく、focused test でも legacy wording を直接流し込む case が残っているだけだったので、current contract に対してノイズになっていた。

目的:
- relative import の live diagnostic contract から legacy `unsupported_import_form` fallback を外す。
- focused common/tooling test を current `relative_import_escape` surface に揃える。
- live docs / plan / source contract における relative import 診断の canonical wording を一本化する。

対象:
- `transpile_cli.py` の legacy `unsupported_import_form` relative-import fallback の削除
- legacy relative-import wording を前提にした focused test の更新
- current `relative_import_escape` diagnostic contract の docs/source contract 固定

非対象:
- relative import 機能そのものの拡張
- import graph algorithm の変更
- archive docs の過去履歴書き換え
- wildcard / duplicate binding 診断の redesign

受け入れ基準:
- live source において relative import 用の `unsupported_import_form` fallback が消えていること。
- focused import-diagnostic / CLI regression が current `relative_import_escape` surface 前提で通ること。
- `python3 tools/build_selfhost.py` が通ること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S1-01] live plan/TODO と acceptance criteria を固定し、legacy relative-import fallback の live producer/consumer を棚卸しする。
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S2-01] `transpile_cli.py` から relative import 用の `unsupported_import_form` / legacy message fallback を外し、focused import diagnostic test を current contract に揃える。
- [x] [ID: P1-RELATIVE-IMPORT-LEGACY-DIAGNOSTIC-CLEANUP-01-S2-02] CLI / backend smoke / source contract を current `relative_import_escape` wording に揃え、archive-ready end state を固める。

決定ログ:
- 2026-03-12: relative import normalization decomposition を archive へ移した後、next cleanup target として live diagnostic からの legacy `unsupported_import_form` relative-import fallback を起票した。current producer は実質なく、focused common test にだけ legacy wording が残っている。
- 2026-03-12: `S1-01` の棚卸しで、live source の producer は `relative_import_escape` だけで、`unsupported_import_form` relative-import lane は `transpile_cli.py` の fallback と `test_import_diagnostics.py` の direct injection case だけだと確定した。
- 2026-03-12: `S2-01` で `transpile_cli.py` から `unsupported_import_form` / `relative import is not supported` fallback を削除し、focused import diagnostic test は `None` を期待する legacy-no-longer-supported case へ切り替えた。
- 2026-03-12: `S2-02` で CLI / backend smoke / source contract を `relative_import_escape` wording に揃え、legacy relative-import wording は negative regression にのみ残す形で archive-ready end state を固定した。
