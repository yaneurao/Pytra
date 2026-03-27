<a href="../../../en/plans/archive/20260312-p1-relative-import-alias-hardening.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import alias の representative contract を固定する

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01`

背景:
- sibling / parent relative `from-import` 自体は実装済みで、`from .helper import f`、`from ..util import two`、`from .. import helper` は representative regression で固定されている。
- ただし `as` alias を伴う relative import は current support が docs / focused test で十分に閉じられていない。
- Pytra-NES のような nested package layout では `from .. import helper as h` や `from ..helper import f as g` のような alias 付き relative import を使う余地があり、ここが regression 未固定だと再発時の検知が遅れる。

目的:
- alias を伴う relative `from-import` の current support を import graph / CLI / C++ multi-file smoke / spec-support に揃えて固定する。

対象:
- `from .helper import f as g`
- `from ..helper import f as g`
- `from .. import helper as h`
- import graph / module metadata 上の alias carrier
- `py2x.py --target cpp` single-file / multi-file regression
- support matrix / import spec の representative 例

非対象:
- relative import 自体の新規実装
- `import .m` のような Python 非合法構文
- wildcard import の新規機能追加
- relative import root escape policy の変更

受け入れ基準:
- `from .. import helper as h` が import graph と CLI / C++ smoke で current support として通る。
- `from ..helper import f as g` と `from .helper import f as g` が CLI / C++ smoke で current support として通る。
- import graph / metadata で module alias は `binding_kind=module`、symbol alias は `import_symbols` 側へ正規化される。
- spec / support matrix が alias representative case を明示し、実装済み contract と矛盾しない。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_relative_import_semantics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import_alias`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO empty 後の follow-up として、relative import の current support を Pytra-NES 型 alias case まで representative regression で固定する `P1` を起票した。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S1-01] alias relative import の target contract と representative scope を plan / TODO に固定する。
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S2-01] import graph / normalization focused test で module alias と symbol alias の metadata carrier を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S2-02] `py2x.py` と C++ multi-file smoke で alias relative import の current support を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-ALIAS-HARDENING-01-S3-01] spec-import / C++ support matrix の representative 例を alias case まで同期する。

- 2026-03-12: current implementation が `from .. import helper as h` と `from ..helper import f as g` を受理することを確認し、import graph / CLI / C++ multi-file build-run regression を追加して `S2-01` / `S2-02` を完了にした。
- 2026-03-12: `validate_from_import_symbols_or_raise()` でも importer 側 `__init__.py` chain を基準に relative `module_id` を normalize するようにして、raw relative carrier が残る focused import-graph test でも alias symbol binding が absolute `module_id` に揃うようにした。
- 2026-03-12: `spec-import` と C++ support matrix に alias representative case を追記し、`from .. import helper as h` / `from ..helper import f as g` を current support contract として docs まで閉じた。
