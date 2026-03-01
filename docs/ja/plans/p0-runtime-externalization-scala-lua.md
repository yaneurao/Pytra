# P0: Scala/Lua runtime 外出し（inline helper 撤去）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-EXT-SCALA-LUA-01`

背景:
- `sample/scala/*.scala` は生成コード内に runtime helper を inline 展開しており、`py_runtime.scala` のような別ファイル参照になっていない。
- `sample/lua/*.lua` も同様に `__pytra_*` helper を先頭へ inline 展開しており、runtime 正本を分離管理できていない。
- 既存の Go/Java/Kotlin/Swift/Ruby/Rust などは runtime 分離が進んでおり、Scala/Lua だけ運用が不統一になっている。

目的:
- Scala/Lua の generated source から runtime helper 本体を撤去し、runtime を別ファイル参照へ統一する。
- runtime 実装の正本を `src/runtime/<lang>/pytra/` に置き、transpile 出力時に同一ディレクトリへ配置する。

対象:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `src/hooks/lua/emitter/lua_native_emitter.py`
- `src/py2scala.py`
- `src/py2lua.py`
- `src/runtime/scala/pytra/*`（新設）
- `src/runtime/lua/pytra/*`（新設）
- `tools/check_py2scala_transpile.py`
- `tools/check_py2lua_transpile.py`
- `tools/runtime_parity_check.py`（必要時）

非対象:
- runtime API 仕様の全面変更
- Scala/Lua backend の性能最適化（cast/loop 縮退など）
- 他言語 backend の runtime 再設計

受け入れ基準:
- `sample/scala/*.scala` と `sample/lua/*.lua` に runtime helper 本体（`__pytra_int` など）が inline 出力されない。
- `py2scala` / `py2lua` 実行時に runtime ファイルが出力先へ配置される。
- Scala/Lua の transpile チェックで runtime 分離契約（inline 禁止 + runtime ファイル存在）を検証できる。
- `sample` の parity チェック（最低 `01_mandelbrot`）で非退行を確認できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/regenerate_samples.py --langs scala,lua --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala,lua 01_mandelbrot --ignore-unstable-stdout`

分解:
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-01] Scala/Lua の inline helper 出力箇所と runtime API 依存を棚卸しし、外出し境界を確定する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-02] runtime ファイル配置規約（パス/ファイル名/読み込み方式）を仕様化する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-01] Scala runtime 正本（`src/runtime/scala/pytra/py_runtime.scala`）を整備する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-02] Scala emitter の inline helper 出力を撤去し、`py2scala.py` で runtime 配置を実装する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-03] Lua runtime 正本（`src/runtime/lua/pytra/py_runtime.lua`）を整備する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-04] Lua emitter の inline helper 出力を撤去し、`py2lua.py` で runtime 配置と読み込み導線を実装する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S3-01] transpile チェック/smoke/parity を更新し、runtime 分離の回帰検知を固定する。

決定ログ:
- 2026-03-02: ユーザー指示により、Scala/Lua runtime 分離を P0 最優先として新規起票した。
