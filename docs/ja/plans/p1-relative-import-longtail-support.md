# P1: relative import long-tail support implementation

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01`

背景:
- C++ は multi-file build/run smoke で relative import baseline を既に満たしている。
- `rs/cs/go/java/js/kotlin/nim/scala/swift/ts` は transpile smoke baseline を持つ一方、`lua/php/ruby` は archived long-tail bundle により `fail_closed_locked + backend_native_fail_closed` baseline のまま残っている。
- archived support rollout plan は handoff だけを固定して終了しており、実際の support 実装を進める live plan が無い。
- Pytra-NES 実験では package 構成の Python を C++ へ流したいので、relative import support の staged rollout を前倒しする必要がある。

目的:
- `lua/php/ruby` の representative relative import project を staged rollout で support する。
- まず Lua backend で `from .. import helper as h` / `from ..helper import f as g` を transpile 成功させ、wildcard relative import だけ fail-closed に維持する。
- backend coverage / parity docs / support contract を bundle の current state に同期する。

対象:
- Lua native emitter の relative import alias rewrite 実装
- relative import support contract / backend coverage inventory / parity docs の staged state 更新
- Lua smoke / tooling checker / backend-local contract の success lane 追加

非対象:
- wildcard relative import support
- PHP / Ruby support 実装
- C++/Rust/C# relative import path の再設計

受け入れ基準:
- Lua backend は representative scenario 2 件を transpile 成功し、`h.f()` / `g()` が `helper.f()` へ rewrite された出力を返す。
- Lua backend は `from ..helper import *` を引き続き `unsupported relative import form: wildcard import` で fail-closed にする。
- backend coverage inventory は `lua` を `transpile_smoke_locked + native_emitter_function_body_transpile` へ更新し、`php/ruby` だけを fail-closed residual として残す。
- long-tail support contract / Lua support contract / backend parity docs が current rollout state と focused smoke lane を正しく記録する。

確認コマンド:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_longtail_support_contract.py`
- `python3 tools/check_relative_import_lua_support_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_lua_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/lua -p 'test_py2lua_smoke.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: archived support rollout plan は handoff 履歴として残し、live 実装計画は同じ `p1-relative-import-longtail-support.md` path で再起票する。
- 2026-03-12: first implementation bundle は Lua backend のみを対象にし、PHP/Ruby は contract 上 fail-closed residual として残す。
- 2026-03-12: Lua support は Go/Nim/Swift と同じ relative-import alias rewrite 方式を使い、representative smoke は direct native-emitter transpile lane で固定する。

## 分解

- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01] `lua/php/ruby` staged rollout を進め、relative import support の current state を docs / tooling / backend coverage へ同期する。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S1-01] active plan / TODO / support handoff を live 実装用に再起票する。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-01] Lua native emitter に relative import alias rewrite を入れ、representative smoke と contract を success lane に切り替える。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-02] PHP backend を同じ representative scenario へ広げ、contract / smoke / parity docs を更新する。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-03] Ruby backend を同じ representative scenario へ広げ、contract / smoke / parity docs を更新する。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S3-01] backend coverage / parity docs / archived handoff wording を final rollout state に同期して task を閉じる。
