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
- [ ] `super` 呼び出しを親テーブル明示呼び出しへ lower する。
- [ ] `setmetatable` 継承チェーンとの整合を確認する。
- [ ] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Lua は metatable 継承上で `super` lower を先行実装する方針とした。
