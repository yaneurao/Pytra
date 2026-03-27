<a href="../../ja/plans/p0-image-runtime-core-gen-rollout.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-image-runtime-core-gen-rollout.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-image-runtime-core-gen-rollout.md`

# P0: 画像runtime 構成是正（`pytra-core` / `pytra-gen` 分離 + 正本自動生成）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-IMAGE-RUNTIME-CORE-GEN-01`

背景:
- 既存の `P0-IMAGE-RUNTIME-SOT-LANG-01` は、marker 付与中心で「正本由来」を扱っており、`py_runtime.*` へ生成相当コードを直埋めする運用を許してしまっている。
- ユーザー方針として、画像runtime（`png.py` / `gif.py` 由来）は C++ と同様に `pytra-gen` へ隔離し、`pytra-core` には手書き共通runtimeのみを置く必要がある。
- したがって、旧P0は実現方式が誤っており、TODOから除去して新方式へ再起票する。

目的:
- 全言語 runtime の画像実装を `pytra-core` から排除し、`pytra-gen`（正本自動生成物）へ統一する。
- backend/runtime hook/parity/監査を新レイアウト前提に再固定し、再発を機械的に防止する。

対象:
- `src/runtime/<lang>/...`（画像runtime配置）
- 画像runtime生成導線（`src/pytra/utils/png.py`, `src/pytra/utils/gif.py` からの生成）
- backend runtime copy hook
- `tools/audit_image_runtime_sot.py` と parity 導線
- `docs/ja/spec` / `docs/en/spec`

非対象:
- 画像以外の runtime API 大規模改修
- README ベンチマーク表更新
- C++ 既存 `pytra-core/pytra-gen` レイアウトの再設計

受け入れ基準:
- 全言語で、画像runtime実装本体（`write_rgb_png`/`save_gif`/`grayscale_palette`）が `pytra-gen` 側にのみ存在する。
- `pytra-core` 側には画像実装本体が存在せず、必要な橋渡しコードのみ許可される。
- 生成物には `source: src/pytra/utils/{png,gif}.py` と生成痕跡が残り、`tools/audit_image_runtime_sot.py` で検査可能である。
- `sample/01` と `sample/05` の parity（stdout + artifact size + CRC32）が全対象言語で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --probe-transpile --summary-json <log>`
- `python3 tools/runtime_parity_check.py --case-root sample --targets <lang> 01_mandelbrot 05_mandelbrot_zoom --ignore-unstable-stdout --summary-json <log>`

## 分解

- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S1-01] 旧 `P0-IMAGE-RUNTIME-SOT-LANG-01` 廃止を反映し、旧方式（marker中心）を無効化する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S1-02] `pytra-core` / `pytra-gen` 責務境界を spec に追記する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-01] 画像runtime生成導線と出力先規約を全言語共通で実装する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S2-02] 監査スクリプトを新方式（物理分離・混入禁止）へ更新する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-RS] Rust を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-GO] Go を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JAVA] Java を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-SWIFT] Swift を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-KOTLIN] Kotlin を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-RUBY] Ruby を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-LUA] Lua を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-PHP] PHP を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-CS] C# を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JS] JavaScript を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-TS] TypeScript を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-SCALA] Scala3 を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-NIM] Nim を `pytra-core` / `pytra-gen` 分離へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-01] 全言語 `sample/01,05` parity（stdout + artifact size + CRC32）を再確認する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-02] backend runtime copy hook / build手順を新レイアウトへ更新する。
- [x] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-03] `pytra-core` 画像実装混入禁止チェックを CI/ローカルへ導入する。

決定ログ:
- 2026-03-04: ユーザー指示により、旧 `P0-IMAGE-RUNTIME-SOT-LANG-01` は「間違った実現方式」と判定してTODOから削除。新方式（`pytra-core` / `pytra-gen` 分離）へ再起票した。
- 2026-03-04: `S1-02` 完了。`docs/ja/spec/spec-{codex,dev}.md` と `docs/en/spec/spec-{codex,dev}.md` に `pytra-core` / `pytra-gen` 境界（core直書き禁止、gen生成痕跡必須）を明文化した。
- 2026-03-04: `S2-01` 完了。`tools/gen_image_runtime_from_canonical.py` を追加し、`png.py/gif.py` から14言語の `src/runtime/<lang>/pytra-gen/...` へ出力する共通生成導線を実装。`--targets cpp,cs,js,ts --dry-run` と `test/unit/tooling/test_gen_image_runtime_from_canonical.py` で導線確認。
- 2026-03-04: `S2-02` 完了。`tools/audit_image_runtime_sot.py` を core/gen レイアウト監査へ置換し、`pytra-core` 混入・`pytra-gen` marker不足・legacy配置残存を検知可能化。`work/logs/image_runtime_core_gen_audit_20260304_s2_02.json` で `compliant=1/non_compliant=13` の移行ベースラインを固定。
- 2026-03-04: `S3-RS` 完了。Rust runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.rs` の画像本体を `pytra-gen/utils/image_runtime.rs` へ移設。`backend_registry(_static)` の Rust runtime hook を core+gen コピーへ更新し、`work/logs/runtime_parity_sample_rs_0105_core_gen_split_retry_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-GO` 完了。Go runtime を `pytra-core`/`pytra-gen` へ分離し、画像本体を `pytra-gen/utils/{png.go,gif.go}` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Go 実行導線を `py_runtime.go + png.go + gif.go` に更新し、`work/logs/runtime_parity_sample_go_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-JAVA` 完了。Java runtime を `pytra-core`/`pytra-gen` へ分離し、`PyRuntime.java` の画像本体を `pytra-gen/utils/{png.java,gif.java}` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Java 実行導線を `PyRuntime + PngHelper + GifHelper` へ更新し、`work/logs/runtime_parity_sample_java_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-SWIFT` 完了。Swift runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.swift` の画像本体（`__pytra_to_u8`〜`__pytra_save_gif`）を `pytra-gen/utils/image_runtime.swift` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Swift 実行導線を `py_runtime + image_runtime` へ更新し、`work/logs/runtime_parity_sample_swift_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-KOTLIN` 完了。Kotlin runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.kt` の画像本体（`__pytra_write_rgb_png`〜`__pytra_save_gif`）を `pytra-gen/utils/image_runtime.kt` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Kotlin 実行導線を `py_runtime + image_runtime` へ更新し、`work/logs/runtime_parity_sample_kotlin_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-RUBY` 完了。Ruby runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.rb` の画像本体（`__pytra_u16le` 以降）を `pytra-gen/utils/image_runtime.rb` へ移設。`py_runtime.rb` から `require_relative \"image_runtime\"` で読込む導線へ変更し、`backend_registry(_static)` の Ruby runtime hook を core+gen コピーへ更新。`work/logs/runtime_parity_sample_ruby_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-LUA` 完了。Lua runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.lua` の画像本体（`__pytra_u16le`〜`__pytra_png_module`）を `pytra-gen/utils/image_runtime.lua` へ移設。`py_runtime.lua` に相対 `dofile(\"image_runtime.lua\")` ローダを追加し、`backend_registry(_static)` の Lua runtime hook を core+gen コピーへ更新。`work/logs/runtime_parity_sample_lua_0105_core_gen_split_20260304.json` で `sample/01 pass / 05 CRC mismatch`（legacy runtime 同値）を確認。
- 2026-03-04: `S3-PHP` 完了。PHP runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.php` は core helper のみに縮退、画像本体を `pytra-gen/runtime/{png.php,gif.php}` へ再配置（`grayscale_palette` を GIF 側へ集約）。`_copy_php_runtime` を新レイアウト読込へ更新し、`work/logs/runtime_parity_sample_php_0105_core_gen_split_20260304_retry.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-CS` 完了。C# runtime を `src/runtime/cs/pytra-core/{built_in,std}` と `src/runtime/cs/pytra-gen/utils` へ分離し、`tools/runtime_parity_check.py`・`tools/check_multilang_selfhost_stage1.py`・`tools/check_multilang_selfhost_multistage.py`・`tools/check_cs_single_source_selfhost_compile.py`・`tools/gen_cs_image_runtime_from_canonical.py` の参照を新レイアウトへ更新。`work/logs/runtime_parity_sample_cs_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-JS` 完了。JavaScript runtime を `src/runtime/js/pytra-core/{built_in,std}` と `src/runtime/js/pytra-gen/utils` へ分離し、`src/toolchain/misc/js_runtime_shims.py` と JS selfhost 検証導線（`check_multilang_selfhost_stage1/multistage`）の runtime 参照を新パスへ更新。`test/unit/common/test_js_ts_runtime_dispatch.py` の JS runtime パスも同期し、`work/logs/runtime_parity_sample_js_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-TS` 完了。TypeScript runtime を `src/runtime/ts/pytra-core/{built_in,std}` と `src/runtime/ts/pytra-gen/utils` へ分離し、`test/unit/common/test_js_ts_runtime_dispatch.py` の TS runtime 参照を新パスへ更新。`work/logs/runtime_parity_sample_ts_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-SCALA` 完了。Scala runtime の画像実装を `src/runtime/scala/pytra-gen/utils/image_runtime.scala` へ切り出し、`src/runtime/scala/pytra-core/built_in/py_runtime.scala` には core/runtime 本体のみを残す構成へ再配置。`backend_registry(_static)` と `runtime_parity_check` を `py_runtime.scala + image_runtime.scala` 実行に更新し、`work/logs/runtime_parity_sample_scala_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-NIM` 完了。Nim runtime の画像実装を `src/runtime/nim/pytra-gen/utils/image_runtime.nim` へ切り出し、`src/runtime/nim/pytra-core/built_in/py_runtime.nim` から `include "image_runtime.nim"` で読み込む構成へ更新。`backend_registry(_static)` の Nim runtime hook を core+gen コピーへ変更し、`work/logs/runtime_parity_sample_nim_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S4-01` 完了。`cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim` の14言語で `sample/01,05` parity（stdout + artifact size + CRC32）を再実行。Lua `sample/05` の CRC 差分は Lua emitter が `save_gif(delay_cs, loop)` keyword を落としていたことが原因で、`_render_call` で `save_gif` keyword を位置引数へ正規化する修正後、`work/logs/runtime_parity_sample_all_0105_core_gen_split_20260304_retry.json` で `case_pass=2/case_fail=0` を確認。
- 2026-03-04: `S4-02` 完了。runtime copy/build 導線を新レイアウトへ統一（`backend_registry(_static)` の Scala/Nim core+gen copy、`runtime_parity_check` の C#/Scala 実行入力更新、`check_py2{scala,nim}_transpile` の runtime存在検証更新、JS/TS selfhost shim の core/gen 参照化）。`rg "runtime/(cs|js|ts|scala|nim)/pytra/"` 監査で、旧固定参照は legacy ガード用途のみに限定されたことを確認。
- 2026-03-04: `S4-03` 完了。`tools/audit_image_runtime_sot.py` に `--fail-on-core-mix`（`core_contains_image_symbols` を検知したら終了コード1）を追加し、`tools/run_local_ci.py` の必須チェックに組み込み。`work/logs/image_runtime_core_gen_audit_20260304_s4_03_guardrail.json` で core 混入 fail 条件が未該当であることを確認。
