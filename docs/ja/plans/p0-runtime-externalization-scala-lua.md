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
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-01] Scala/Lua の inline helper 出力箇所と runtime API 依存を棚卸しし、外出し境界を確定する。
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-02] runtime ファイル配置規約（パス/ファイル名/読み込み方式）を仕様化する。
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-01] Scala runtime 正本（`src/runtime/scala/pytra/py_runtime.scala`）を整備する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-02] Scala emitter の inline helper 出力を撤去し、`py2scala.py` で runtime 配置を実装する。
- [x] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-03] Lua runtime 正本（`src/runtime/lua/pytra/py_runtime.lua`）を整備する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-04] Lua emitter の inline helper 出力を撤去し、`py2lua.py` で runtime 配置と読み込み導線を実装する。
- [ ] [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S3-01] transpile チェック/smoke/parity を更新し、runtime 分離の回帰検知を固定する。

## S1実施結果（2026-03-02）

### S1-01: inline helper 棚卸しと外出し境界

- Scala:
  - inline runtime 本体は `scala_native_emitter.py` の `_emit_runtime_helpers()` に集中している（`__pytra_*` 54関数）。
  - `transpile_to_scala_native()` では `_emit_runtime_helpers_minimal(...)` を使って必要 helper を生成コードへ挿入している。
  - 外出し境界は「`_emit_runtime_helpers*` が返す helper 群全体」を `py_runtime.scala` へ移管し、emitter 側は import/use のみ行う。
- Lua:
  - inline runtime は `_emit_imports()` 起点で `_emit_*_helper` / `_emit_*_runtime_helpers` を逐次出力している。
  - 主要 emit 関数は `print/repeat/truthy/contains/string predicates/perf_counter/math/path/gif/png/isinstance`（計11系統）。
  - 外出し境界は「`_emit_imports()` で直接生成している helper 本体」を `py_runtime.lua` へ移管し、emitter 側は runtime module 参照のみ行う。
- CLI:
  - `py2scala.py` / `py2lua.py` は現状 runtime 配置処理を持たず、生成コードのみを書き出す。
  - 外出し実装時に CLI へ runtime コピー導線を追加する必要がある。

### S1-02: runtime ファイル配置規約

- 正本配置:
  - Scala: `src/runtime/scala/pytra/py_runtime.scala`
  - Lua: `src/runtime/lua/pytra/py_runtime.lua`
- 生成先配置:
  - `py2scala.py` は `output_path.parent / "py_runtime.scala"` へ runtime をコピーする。
  - `py2lua.py` は `output_path.parent / "py_runtime.lua"` へ runtime をコピーする。
  - 既存 Go/Kotlin/Swift/Ruby/Rust と同じ「出力ファイル隣接配置」規約に揃える。
- fail-closed:
  - runtime 正本が存在しない場合は CLI で `RuntimeError` を投げ、生成成功扱いにしない。
- emitter 側契約:
  - helper 本体文字列を emit しない。
  - runtime ファイルが提供する関数名契約（`__pytra_*`）のみを参照する。

決定ログ:
- 2026-03-02: ユーザー指示により、Scala/Lua runtime 分離を P0 最優先として新規起票した。
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-01] Scala/Lua の inline helper 出力点と runtime API 依存を棚卸しし、外出し境界を「helper本体の runtime 正本移管 + emitter 側は参照専任」に確定した。
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S1-02] runtime 配置規約を「`src/runtime/<lang>/pytra/py_runtime.*` 正本 + `output_path.parent/py_runtime.*` コピー」に確定した。
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-01] `src/runtime/scala/pytra/py_runtime.scala` を追加し、現行 `_emit_runtime_helpers()` の helper 群を正本ファイルへ切り出した。
- 2026-03-02: [ID: P0-RUNTIME-EXT-SCALA-LUA-01-S2-03] `src/runtime/lua/pytra/py_runtime.lua` を追加し、Lua emitter の helper 本体（11系統）を正本ファイルへ切り出した。
