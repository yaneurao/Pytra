# P0: Lua backend 追加（最優先）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LUA-BACKEND-01`

背景:
- ユーザー指示として、Pytra の新規ターゲット言語に Lua を追加する方針が確定した。
- 現状は `py2lua.py` と `src/hooks/lua/` が存在せず、Lua backend は未実装。
- 既存 backend と同様に、責務境界（EAST3 入力・fail-closed・runtime 境界）を先に固定しないと実装肥大化と互換崩れのリスクが高い。

目的:
- `py2lua.py` を入口として `EAST3 -> Lua native` の直生成経路を追加し、`sample/py` の主要ケースを Lua で実行可能にする。

対象:
- `src/py2lua.py`
- `src/hooks/lua/emitter/`
- `src/runtime/lua/pytra/`（必要最小限）
- `tools/check_py2lua_transpile.py` / `test/unit/test_py2lua_smoke.py` / parity 導線
- `sample/lua` と関連ドキュメント

非対象:
- PHP backend の同時追加
- Lua backend の高度最適化（まず正しさと回帰導線を優先）
- 既存 backend（`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby`）の大規模設計変更

受け入れ基準:
- `py2lua.py` で EAST3 から Lua コードを生成できる。
- 最小 fixture（`add` / `if_else` / `for_range`）の変換・実行が通る。
- `tools/check_py2lua_transpile.py` と smoke/parity 回帰導線が用意される。
- `sample/lua` と `docs/ja` 利用手順・対応表が同期される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-28: ユーザー指示により、Lua backend 追加を最優先（P0）として着手する方針を確定した。

## 分解

- [ ] [ID: P0-LUA-BACKEND-01-S1-01] Lua backend の契約（入力 EAST3、fail-closed、runtime 境界、非対象）を `docs/ja/spec` に文書化する。
- [ ] [ID: P0-LUA-BACKEND-01-S1-02] `src/py2lua.py` と `src/hooks/lua/emitter/` の骨格を追加し、最小 fixture を通す。
- [ ] [ID: P0-LUA-BACKEND-01-S2-01] 式/文の基本 lower（代入、分岐、ループ、呼び出し、組み込み最小）を実装する。
- [ ] [ID: P0-LUA-BACKEND-01-S2-02] class/instance/isinstance/import（`math`・画像runtime含む）対応を段階実装する。
- [ ] [ID: P0-LUA-BACKEND-01-S3-01] `check_py2lua_transpile` と smoke/parity 回帰導線を追加する。
- [ ] [ID: P0-LUA-BACKEND-01-S3-02] `sample/lua` 再生成と README/How-to-use 同期を行う。
