<a href="../../../en/plans/archive/20260311-p0-relative-import-project-layout-hardening.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: relative import の project layout hardening

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01`

背景:
- relative import 自体は既に support 済みで、sibling / package-root parent import の representative regression も archive されている。
- ただし、実利用では Pytra-NES のような `pkg/main.py -> .subpkg.mod -> ..util.bits` という project-style layout が使われるため、1-file / 2-file の代表ケースだけでは regressions を早期検知しにくい。
- 現在の test は `from .helper import f` と `from ..util import two` を個別に固定しているが、nested package chain を 1 本で通す entrypoint smoke はない。

目的:
- Pytra-NES のような nested package layout を representative smoke として固定し、relative import support の current contract を project-level で fail-fast にする。
- root escape fail-closed と current diagnostics contract は維持したまま、supported lane と unsupported lane の境界を明確にする。

対象:
- `py2x.py --target cpp` の project-style relative import smoke
- nested package での sibling + parent relative import chain
- `from . import module` / root escape の residual representative regression
- TODO / plan / English mirror の整合

非対象:
- relative import の新仕様追加
- namespace package や `pyproject.toml` ベース root 推定
- wildcard import / absolute import / import graph algorithm の再設計

受け入れ基準:
- nested package project layout で `from .cpu.runner import run` と `from ..util.bits import low_nibble` を含む representative smoke が `py2x.py --target cpp` で通ること。
- `from . import helper` の package-local import も representative regression で current contract を固定すること。
- root escape (`from ...bad import x`) は引き続き `input_invalid(kind=unsupported_import_form)` で fail-closed すること。
- `python3 tools/check/check_todo_priority.py`、対象 unit test、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_import_diagnostics.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-11: active TODO が空になったため、relative import support の residual hardening を follow-up として起票した。新規実装よりも、Pytra-NES 型の nested package layout を regression へ上げることを優先する。
- 2026-03-11: first representative smoke は `pkg/nes/main.py -> from .cpu.runner import run`, `pkg/nes/cpu/runner.py -> from ..util.bits import low_nibble` とし、entrypoint 成功を `py2x.py --target cpp` で固定した。
- 2026-03-11: `from . import helper` は graph 解析が `ImportFrom.module="."` だけを dependency として見ていたため `unsupported_import_form` で落ちていた。dot-only relative `ImportFrom` は `.helper` / `..helper` の package-local submodule candidate として graph へ流す contract に更新した。

## 分解

- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S1-01] current support / residual gap を plan/TODO に固定する。
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S2-01] nested package の project-style relative import smoke を `py2x.py --target cpp` regression に追加する。
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S2-02] `from . import module` と root-escape diagnostics の representative regression を current contract に揃える。
- [x] [ID: P0-RELATIVE-IMPORT-PROJECT-LAYOUT-HARDENING-01-S3-01] docs / archive を更新して閉じる。
