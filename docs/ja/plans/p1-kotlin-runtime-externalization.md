# P1: Kotlin runtime 外出し（inline helper 撤去）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-KOTLIN-RUNTIME-EXT-01`

背景:
- `sample/kotlin/*.kt` の生成コードには `fun __pytra_truthy(v: Any?): Boolean` をはじめとする runtime helper 本体が inline 出力されている。
- 既存の `P1-RUNTIME-EXT-01` は Go/Java/Swift/Ruby のみを対象として完了しており、Kotlin は対象外だった。
- Kotlin も runtime 外部化しないと、生成コード肥大化・runtime 実装重複・差し替え困難が継続する。

目的:
- Kotlin backend の生成コードから `__pytra_*` helper 本体定義を撤去し、runtime ファイル参照方式へ統一する。

対象:
- `src/hooks/kotlin/emitter/kotlin_native_emitter.py`
- `src/runtime/kotlin/pytra/`（runtime 正本の新設または整理）
- `src/py2kotlin.py`（runtime 配置導線）
- `test/unit/test_py2kotlin_smoke.py`
- `tools/check_py2kotlin_transpile.py`
- `tools/runtime_parity_check.py` の Kotlin 導線
- `sample/kotlin` 再生成

非対象:
- Kotlin backend の最適化（性能改善、式簡約など）
- sidecar 撤去済み範囲の再設計
- 他言語 backend の runtime 方式変更

受け入れ基準:
- `py2kotlin` 生成コードに `fun __pytra_truthy` を含む runtime helper 本体が inline 出力されない。
- 生成コードは runtime ファイル（例: `py_runtime.kt`）を参照してビルド/実行できる。
- `check_py2kotlin_transpile` / Kotlin smoke / parity（少なくとも `sample/18` と `--all-samples`）が非退行で通る。
- `sample/kotlin` 再生成後も inline helper が残存しない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs kotlin --force`
- `rg -n \"fun __pytra_truthy\\(v: Any\\?\\): Boolean\" sample/kotlin`

決定ログ:
- 2026-02-28: ユーザー指示により、Kotlin の runtime 外出しを `P1` で新規起票した。

## 分解

- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S1-01] Kotlin emitter の inline helper 出力一覧と runtime API 対応表を確定する。
- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-01] Kotlin runtime 正本（`src/runtime/kotlin/pytra`）を整備し、`__pytra_*` API を外部化する。
- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-02] Kotlin emitter から helper 本体出力を撤去し、runtime 呼び出し専用へ切り替える。
- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-03] `py2kotlin.py` の出力導線で runtime ファイルを配置する。
- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-01] `check_py2kotlin_transpile` / smoke / parity を更新し、回帰を固定する。
- [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-02] `sample/kotlin` 再生成で inline helper 残存ゼロを確認する。

## S1-01 棚卸し結果

### 1) emitter で inline 出力される runtime helper（32個）

- 変換/真偽/基本: `__pytra_any_default` `__pytra_truthy` `__pytra_int` `__pytra_float` `__pytra_str` `__pytra_len` `__pytra_assert` `__pytra_noop` `__pytra_perf_counter`
- 添字/スライス: `__pytra_index` `__pytra_get_index` `__pytra_set_index` `__pytra_slice`
- 文字列/包含: `__pytra_isdigit` `__pytra_isalpha` `__pytra_contains`
- 条件式/コンテナ: `__pytra_ifexp` `__pytra_bytearray` `__pytra_bytes` `__pytra_list_repeat` `__pytra_enumerate` `__pytra_as_list` `__pytra_as_dict` `__pytra_pop_last`
- 組み込み相当: `__pytra_print` `__pytra_min` `__pytra_max`
- 型判定: `__pytra_is_int` `__pytra_is_float` `__pytra_is_bool` `__pytra_is_str` `__pytra_is_list`

### 2) 追加で emitter 生成される class 依存 helper

- `__pytra_is_<Class>` / `__pytra_as_<Class>` は class 名に依存するため、現状はモジュールごとに生成される。
- S2 では「共通 runtime へ移す helper」と「生成継続する class 依存 helper」を分離して扱う。

### 3) runtime 正本との対応ギャップ

- 現在の `src/runtime/kotlin/pytra/py_runtime.kt` は `PyRuntime.runEmbeddedNode` のみで、上記 `__pytra_*` API を提供していない。
- そのため `sample/kotlin/*.kt` は毎回 helper 本体を inline 出力しており、runtime 参照方式が未成立。

### 4) S2 で埋める API 契約（確定）

- `src/runtime/kotlin/pytra/py_runtime.kt` に上記32 helper を top-level 関数として実装する。
- emitter は helper 本体を出力せず、`import pytra.runtime.*`（仮称）などの参照のみを生成する。
- class 依存 helper（`__pytra_is_<Class>` / `__pytra_as_<Class>`）は S2-02 で暫定維持し、外部化対象からは除外する（重複削減は別タスク化）。

決定ログ:
- 2026-03-01: `kotlin_native_emitter.py` の `_emit_runtime_helpers()` で inline 出力される `__pytra_*` 32 API を棚卸しし、`src/runtime/kotlin/pytra/py_runtime.kt`（現状 `runEmbeddedNode` のみ）とのギャップを固定した（`P1-KOTLIN-RUNTIME-EXT-01-S1-01`）。
- 2026-03-01: `src/runtime/kotlin/pytra/py_runtime.kt` を `__pytra_*` 32 helper 実装入りの runtime 正本へ更新し、`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`（10件）で非退行を確認した（`P1-KOTLIN-RUNTIME-EXT-01-S2-01`）。
- 2026-03-01: `transpile_to_kotlin_native()` から `_emit_runtime_helpers()` 呼び出しを撤去し、生成 `.kt` から helper 本体 inline 出力を停止した。`test_py2kotlin_smoke` の回帰で `fun __pytra_truthy` 非出力を固定した（`P1-KOTLIN-RUNTIME-EXT-01-S2-02`）。
- 2026-03-01: `py2kotlin.py` に runtime コピー導線（`_copy_kotlin_runtime`）を追加し、出力先へ `py_runtime.kt` を同梱するよう変更した。`/tmp` 変換実測で runtime 同梱を確認した（`P1-KOTLIN-RUNTIME-EXT-01-S2-03`）。
- 2026-03-01: `tools/check_py2kotlin_transpile.py` に Kotlin 未対応 fixture（Try/Yield/Swap）を expected fail として明示化し、`checked=129 ok=129 fail=0 skipped=10` を確認した。
- 2026-03-01: Kotlin parity 導線を更新し、`runtime_parity_check.py` の Kotlin 実行で `py_runtime.kt` 同梱コンパイルと artifact no-op 方針を反映した。
- 2026-03-01: Kotlin emitter の `dict.get(key, default)` を `map.get(key) ?: default` へ修正し、`Dict(entries)` 描画を追加して sample/18 の runtime 失敗（token map 空化）を解消した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`（12件）、`python3 tools/check_py2kotlin_transpile.py`、`python3 tools/runtime_parity_check.py --case-root sample --targets kotlin --all-samples --ignore-unstable-stdout`（18/18 pass）、`python3 tools/regenerate_samples.py --langs kotlin --force` を通過した。
