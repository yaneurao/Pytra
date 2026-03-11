# P0: `from .. import helper` Relative Import Hardening

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-BARE-PARENT-01`

背景:
- relative `from-import` 本体はすでに実装済みで、`from .helper import f`、`from ..pkg import y`、`from . import helper` は representative test がある。
- ただし `from .. import helper` のような「parent package から submodule をそのまま束縛する」形は、実装上は通るのに current spec / tutorial / support matrix に例として出ていない。
- Pytra-NES のような package-local multi-file project では `from .. import helper` が自然に現れるため、この lane が「たまたま通る」状態のままだと再退行しやすい。
- 実装済みなのに spec が弱い状態は、利用者から見ると未対応に見える。ここは parser / frontend / import graph / CLI / C++ multi-file smoke の representative contract を揃えるべき段階である。

目的:
- `from .. import helper` を current supported relative import contract の一部として明示する。
- CLI / import graph / C++ multi-file で representative regression を追加し、project-style package layout で再退行しないようにする。
- docs / spec / support matrix / tutorial を current implementation に同期し、「relative import 未対応」に見える説明をなくす。

対象:
- relative import user-facing contract の明文化
- `py2x.py --target cpp` の representative success regression
- import graph / carrier layer の representative regression
- C++ support matrix / tutorial / spec の同期

非対象:
- relative import の新規実装
- `import .m` のような非合法 Python syntax
- runtime dynamic import
- namespace package 完全互換

受け入れ基準:
- `pkg/sub/main.py -> from .. import helper` が `py2x.py --target cpp` で成功する representative test があること。
- import graph / validation が `from .. import helper` を package-local submodule import として扱う representative test があること。
- `spec-import.md` / `spec-user.md` / tutorial / C++ support matrix が `from .. import helper` を current supported form として明記していること。
- root escape (`from ...oops import x`) fail-closed と既存 relative import representative regression を壊さないこと。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_graph_issue_structure.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `git diff --check`

分解:
- [ ] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S1-01] `from .. import helper` を current supported contract として plan/spec に固定する。
- [ ] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S2-01] CLI / import graph の representative regression を追加して package-parent bare import success を固定する。
- [ ] [ID: P0-RELATIVE-IMPORT-BARE-PARENT-01-S2-02] C++ multi-file smoke と support matrix / tutorial の記述を current contract に同期する。

決定ログ:
- 2026-03-12: TODO 空き後の新規 P0 として起票。probe では `pkg/sub/main.py -> from .. import helper` はすでに成功したため、新規実装ではなく representative contract の close-out として扱う。
