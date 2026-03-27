<a href="../../../en/plans/archive/20260314-p0-relative-wildcard-import-native-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: relative wildcard import native backend rollout

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01`

背景:
- C++ multi-file lane では `from .helper import *` が representative smoke で既に lock されている。
- 一方、non-C++ の native backend では `from ..helper import *` / `from .helper import *` が backend 側で `unsupported relative import form: wildcard import` を返す lane が残っている。
- relative import 自体は多くの backend で transpile smoke まで進んでいるため、wildcard だけが別 contract で取り残されている。
- Pytra-NES のような multi-file project では import surface の差が blocker になるので、relative wildcard import も representative lane から順に揃える必要がある。

目的:
- non-C++ native backend でも representative `from .helper import *` / `from ..helper import *` を既存 import resolution contract の上で扱えるようにする。
- 解決不能ケースや duplicate binding は現在の absolute wildcard import と同じく fail-closed に維持する。

対象:
- `go/java/kotlin/lua/nim/php/ruby/scala/swift` backend の relative wildcard import lane
- backend-native emitter / package transpile での relative wildcard import regression
- rollout contract / checker / docs / TODO の同期

非対象:
- C++ lane の再設計
- `from helper import *` の absolute wildcard import 意味論変更
- `rs/cs/js/ts` backend への横展開
- dynamic import や runtime import hook

受け入れ基準:
- target backend の representative smoke が `from .helper import *` または `from ..helper import *` を transpile success すること。
- duplicate binding / unresolved wildcard / root escape は引き続き fail-closed すること。
- 既存の non-wildcard relative import smoke を壊さないこと。
- `python3 tools/check_todo_priority.py`、focused backend smoke、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_relative_wildcard_import_native_rollout_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_wildcard_import_native_rollout_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-13: TODO が空のため、Pytra-NES 系の import blocker に近い follow-up として relative wildcard import native rollout を `P0` で起票した。最初は current fail-closed inventory を exact に固定し、bundle 単位で rollout する。
- 2026-03-13: `S1-01` / `S1-02` として rollout bundle、evidence lane、current fail-closed inventory を contract/checker/unit test で固定した。次は `go/nim/swift` の native-path bundle を green にする。
- 2026-03-13: `go/nim/swift` は backend emitter だけを更新し、single-file `load_east3_document(...)` lane は fail-closed のまま、module-graph `build_module_east_map(...)` lane だけを wildcard-expanded `meta.import_symbols` 経由で green にした。次は `java/kotlin/scala` の package-project bundle を揃える。
- 2026-03-13: `java/kotlin/scala` も single-file `load_east3_document(...)` lane は fail-closed を維持しつつ、module-graph `build_module_east_map(...)` lane では wildcard-expanded `meta.import_symbols` を使って representative package bundle を green にした。次は `lua/php/ruby` の long-tail bundle を揃える。
- 2026-03-14: `lua/php/ruby` も single-file `load_east3_document(...)` lane は fail-closed を維持しつつ、module-graph `build_module_east_map(...)` lane では wildcard-expanded `meta.import_symbols` を使って representative long-tail bundle を green にした。残りは docs / parity sync だけになった。
- 2026-03-14: coverage / parity docs / contract handoff を final state に同期し、native wildcard import rollout は representative module-graph bundle `transpile_smoke_locked`・single-file direct lane `backend_specific_fail_closed` の end state で close した。

## 分解

- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S1-01] plan / TODO に rollout 順と representative backend bundle を固定する。
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S1-02] current fail-closed backend inventory と evidence lane を contract / checker / unit test で固定する。
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-01] `go/nim/swift` native-path bundle の relative wildcard import を representative smoke で green にする。
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-02] `java/kotlin/scala` package-project bundle の relative wildcard import を representative smoke で green にする。
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-03] `lua/php/ruby` long-tail native-emitter bundle の relative wildcard import を representative smoke で green にする。
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S3-01] backend coverage / parity docs / TODO を final state に同期して task を閉じる。
