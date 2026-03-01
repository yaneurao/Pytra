# P0: sample/lua/01 runtime マッピング是正（最優先）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LUA-SAMPLE01-RUNTIME-01`

背景:
- `sample/lua/01_mandelbrot.lua` は import マッピング未実装により、機能欠落を含む生成コードになっている。
- 具体的には以下。
  - `from time import perf_counter` が `not yet mapped` コメント化される。
  - `pytra.runtime.png` が no-op stub（`write_rgb_png = function(...) end`）へ退化する。
- この状態では `sample/lua/01` の I/O 実行結果が正しく保証されず、benchmark/parity の前提を満たさない。

目的:
- Lua backend における `perf_counter` / PNG writer の import マッピングを実機能へ接続し、no-op 退化を撤去する。

対象:
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/runtime/lua/*`（必要に応じて新設）
- `test/unit/test_py2lua_smoke.py`（または Lua 専用 test）
- `sample/lua/01_mandelbrot.lua` 再生成結果

非対象:
- Lua backend 全体の性能最適化
- `sample/lua/01` 以外の冗長表現整理（別 P1 で扱う）
- 他言語 backend の同時改修

受け入れ基準:
- `sample/lua/01_mandelbrot.lua` に `not yet mapped` コメントが残らない。
- `png.write_rgb_png` が no-op ではなく runtime の実実装呼び出しになる。
- `perf_counter` が Lua runtime 経由で解決される。
- 未解決 import は暗黙 no-op にせず fail-closed で検知できる。
- transpile/smoke/parity 導線が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/regenerate_samples.py --langs lua --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua 01_mandelbrot`

分解:
- [ ] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S1-01] `time.perf_counter` import の Lua runtime マッピングを実装し、`not yet mapped` コメント生成を禁止する。
- [ ] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S2-01] `pytra.runtime.png` / `pytra.utils.png` を no-op stub ではなく実 runtime 呼び出しへ接続する。
- [ ] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S2-02] 未解決 import の no-op フォールバックを撤去し、fail-closed（明示エラー）へ変更する。
- [ ] [ID: P0-LUA-SAMPLE01-RUNTIME-01-S3-01] 回帰テストを追加し、`sample/lua/01` 再生成 + parity で非退行を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/lua/01` の runtime 機能欠落（time/png no-op）を `P0` で先行是正する方針を確定した。
