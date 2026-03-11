# P1: Import Graph Frontend Decomposition

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01`

背景:
- relative import normalization cluster は dedicated module へ分離できたが、import graph の build/analyze/report helper はまだ [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) と [east1_build.py](/workspace/Pytra/src/toolchain/frontends/east1_build.py) に密集している。
- module queue、module-id fallback、graph issue/report formatting、analysis assembly が entrypoint 直下に残っているため、frontend の責務がまだ重い。
- selfhost / CLI / import graph regression はすでに存在するので、次は algorithm を変えずに cluster を dedicated module へ寄せる段階である。

目的:
- import graph build/analyze/report cluster を dedicated frontend module へ分離する。
- `transpile_cli.py` / `east1_build.py` を orchestration entrypoint に縮める。
- focused tooling/source contract を追加し、以後の import graph 修正を局所化する。

対象:
- import graph path / queue / module-id helper の分離
- import graph analysis / report helper の分離
- frontend entrypoint から split module への寄せ替え
- focused tooling/source contract と既存 regression の維持

非対象:
- import graph algorithm の redesign
- relative import 機能追加
- wildcard / duplicate binding 診断 contract の変更
- runtime import の導入

受け入れ基準:
- representative import graph helper cluster が `transpile_cli.py` / `east1_build.py` 直下から dedicated frontend module へ分離されていること。
- focused tooling/source contract が split 後の helper 所在を固定していること。
- existing import graph / CLI / selfhost regression が通ること。
- `python3 tools/build_selfhost.py` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_relative_import_normalization_source_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S1-01] live plan/TODO を起票し、split 対象 cluster と verification lane を固定する。
- [ ] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S2-01] path / queue / module-id helper を dedicated module へ切り出し、entrypoint caller を寄せ替える。
- [ ] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S2-02] analysis / report helper を dedicated module へ切り出し、focused tooling/source contract を追加する。
- [ ] [ID: P1-IMPORT-GRAPH-FRONTEND-DECOMPOSITION-01-S3-01] residual helper layout を docs/source contract に固定し、archive-ready end state を閉じる。

決定ログ:
- 2026-03-12: relative import normalization decomposition と legacy diagnostic cleanup を閉じた後の次 task として、残存する import graph build/analyze/report cluster を focused decomposition target に選んだ。algorithm redesign ではなく frontend module split に限定する。
