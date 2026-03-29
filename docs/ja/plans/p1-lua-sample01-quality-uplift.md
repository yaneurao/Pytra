<a href="../../en/plans/p1-lua-sample01-quality-uplift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- `tools/unittest/test_py2lua_smoke.py`（コード断片回帰）
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
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs lua --force`

分解:
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] `sample/lua/01` の冗長箇所（暗黙runtime依存 / nil初期化 / ループ表現）をコード断片で固定する。
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] `int/float/bytearray` など runtime 依存の出力を明示化し、自己完結性を改善する。
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] typed 経路で `r/g/b` の不要な `nil` 初期化を削減する。
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] 単純 `range` ループの step/括弧出力を簡素化する fastpath を追加する。
- [x] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] 回帰テストを追加し、`sample/lua/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/lua/01` の可読性/冗長性改善を `P1` として計画化した。
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] 現行 `sample/lua/01_mandelbrot.lua` の冗長断片を固定し、実装優先順を `runtime依存明示 -> nil初期化削減 -> loop簡素化` に確定。
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] `int/float/bytearray/bytes` を inline 展開から `__pytra_*` runtime helper 呼び出しへ統一し、`sample/lua/01` を runtime 別ファイル参照 + 明示 helper 依存へ更新。
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] scalar型 `AnnAssign(value=None)` を `local name` 出力へ縮退し、`sample/lua/01` の `local r/g/b = nil` を撤去。
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] 単純 `range` ループで `step=1` を省略し、simple bound は `n - 1` 形式へ簡素化。`continue` 非使用ループの `::__pytra_continue_*::` も非出力化。
- 2026-03-02: [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] `test_py2lua_smoke.py` に `sample01` 品質回帰断片（runtime helper利用/nil撤去/loop簡素化）を固定し、`check_py2lua_transpile` と `runtime_parity_check --targets lua 01_mandelbrot` pass を確認。

## S1-01 棚卸し結果

固定断片（`sample/lua/01_mandelbrot.lua`）:

- 暗黙 runtime 依存:
  - `local perf_counter = __pytra_perf_counter`
  - `local png = __pytra_png_module()`
  - `png.write_rgb_png(out_path, width, height, pixels)`
  - 生成物冒頭に runtime helper 群が直接展開される（自己説明性が低い）。
- 不要 `nil` 初期化:
  - `local r = nil`
  - `local g = nil`
  - `local b = nil`
- ループ冗長:
  - `for y = 0, (height) - 1, 1 do`
  - `for x = 0, (width) - 1, 1 do`
  - `for i = 0, (max_iter) - 1, 1 do`
  - `::__pytra_continue_2::` / `::__pytra_continue_3::` が単純ループにも出力される。

実装優先順:

1. `S2-01`: runtime 依存 API の明示化（呼び出し面の自己完結性改善）
2. `S2-02`: typed 経路の `nil` 初期化撤去
3. `S2-03`: loop の `, 1` / 過剰括弧 / 不要 continue label の簡素化
