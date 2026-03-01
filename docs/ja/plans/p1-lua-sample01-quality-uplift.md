# P1: sample/lua/01 品質改善（可読性・冗長性の縮小）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-LUA-SAMPLE01-QUALITY-01`

背景:
- `sample/lua/01_mandelbrot.lua` は機能面とは別に、C++ 出力と比較して可読性/冗長性の品質差が大きい。
- 主な差分は以下。
  - `int/float/bytearray` など runtime 依存が暗黙で、コード単体の自己説明性が低い。
  - `r/g/b = nil` の不要な一時初期化が残る。
  - `for ... , 1 do` と過剰括弧が多く、読みにくい。

目的:
- `sample/lua/01` 出力の可読性を改善し、冗長コードを削減する。

対象:
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/runtime/lua/*`（必要に応じて）
- `test/unit/test_py2lua_smoke.py`（コード断片回帰）
- `sample/lua/01_mandelbrot.lua` の再生成

非対象:
- runtime 機能欠落（time/png no-op）の是正（P0 で先行）
- Lua backend 全体への一括適用
- EAST3 仕様の大規模変更

受け入れ基準:
- `sample/lua/01_mandelbrot.lua` の runtime 依存表現を明示化し、暗黙依存を減らす。
- `r/g/b` など typed 経路で不要な `nil` 初期化を削減する。
- 単純 `range` 起点ループで不要な step/括弧表現を減らす。
- 既存の transpile/smoke/parity が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/regenerate_samples.py --langs lua --force`

分解:
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] `sample/lua/01` の冗長箇所（暗黙runtime依存 / nil初期化 / ループ表現）をコード断片で固定する。
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] `int/float/bytearray` など runtime 依存の出力を明示化し、自己完結性を改善する。
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] typed 経路で `r/g/b` の不要な `nil` 初期化を削減する。
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] 単純 `range` ループの step/括弧出力を簡素化する fastpath を追加する。
- [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] 回帰テストを追加し、`sample/lua/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/lua/01` の可読性/冗長性改善を `P1` として計画化した。
