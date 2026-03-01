# P0: Lua 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA`

背景:
- Lua backend は `setmetatable` 継承を持つが、`super` 相当呼び出しの lower が不足している。

目的:
- Lua で親メソッド呼び出しを明示的に生成し、継承呼び出しの一貫性を確保する。

対象:
- `src/hooks/lua/emitter/lua_native_emitter.py`

非対象:
- Lua runtime 全般の最適化

受け入れ基準:
- `super` 呼び出し用 helper/出力規則が導入される。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets lua`

分解:
- [x] `super` 呼び出しを親テーブル明示呼び出しへ lower する。
- [x] `setmetatable` 継承チェーンとの整合を確認する。
- [x] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Lua は metatable 継承上で `super` lower を先行実装する方針とした。
- 2026-03-01: class method emit 時に現在クラス/基底クラス文脈を保持し、`super().method(...)` を `Base.method(self, ...)` へ lower する規則を追加した。
- 2026-03-01: `py_assert_stdout` import stub を副作用なし（関数実行なし）に更新し、assert 経路で不要 stdout が出ないようにした。
- 2026-03-01: `test_py2lua_smoke.py`（33 tests）と `runtime_parity_check --targets lua`（1/1 pass）で継承 dispatch fixture の一致を確認した。
