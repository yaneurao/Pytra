<a href="../../../en/plans/archive/20260312-p1-relative-import-normalization-decomposition.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: Relative Import Normalization Decomposition

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01`

背景:
- relative import support 自体はすでに実装済みで、`from .helper import f` / `from ..pkg import y` / `from .. import helper` の representative regression もある。
- ただし package-root 推定、relative module 正規化、EAST metadata rewrite の helper 群が [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) に密集したままで、frontend の責務が重い。
- この cluster は import graph / CLI / selfhost の基礎契約でもあるため、単に動いているだけではなく、focused module と focused test に分けて保守可能にする段階に来ている。

目的:
- `transpile_cli.py` に残る relative import 正規化 cluster を dedicated module へ分離する。
- package-root/path helper と relative import semantics を focused test で固定し、import graph / CLI regression は既存 suite で維持する。
- `transpile_cli.py` の責務を縮め、以後の relative import 拡張や bugfix を局所化する。

対象:
- package-root/path helper の分離
- relative import normalization / rewrite helper の分離
- focused unit test と source contract の追加
- 既存 CLI / import graph / selfhost regression の維持

非対象:
- relative import の新規機能追加
- namespace package 対応の拡張
- import graph algorithm 自体の redesign
- runtime import の導入

受け入れ基準:
- relative import normalization helper が `transpile_cli.py` 直下の巨大 cluster ではなく、dedicated frontend module へ分離されていること。
- package-root/path helper と relative import semantics に focused unit test があること。
- 既存の relative import CLI / import graph regression が通ること。
- `python3 tools/build_selfhost.py` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_relative_import_semantics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S1-01] active plan / TODO / decomposition target を live 化し、split boundary と verification lane を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S2-01] package-root/path helper と relative import normalization helper を dedicated frontend module へ切り出し、focused test を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S2-02] EAST rewrite / import graph caller を split module 前提へ寄せ、source contract と selfhost regression を整える。
- [x] [ID: P1-RELATIVE-IMPORT-NORMALIZATION-DECOMPOSITION-01-S3-01] residual helper layout を source contract と docs に固定し、plan を close できる状態へ整える。

決定ログ:
- 2026-03-12: relative import support の contract close-out 後に、`transpile_cli.py` に残る normalization cluster を次の focused decomposition target として起票した。
- 2026-03-12: `S2-01` では `relative_import_normalization.py` を dedicated module とし、`transpile_cli.py` 側は thin re-export に留める。focused common test で package-root inference、bare parent import、missing/root-escape、EAST metadata rewrite を固定する。
- 2026-03-12: `S2-02` では `east1_build.py` の import graph caller を split module に寄せたうえで、`transpile_cli.py` / `east1_build.py` / `relative_import_normalization.py` の source contract を dedicated tooling test で固定する。
- 2026-03-12: `S3-01` として residual live helper layout を dedicated module + source contract へ固定し、relative import normalization cluster の分解 task は archive へ移せる状態になった。
