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
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-LUA] Lua を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-PHP] PHP を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-CS] C# を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-JS] JavaScript を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-TS] TypeScript を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-SCALA] Scala3 を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S3-NIM] Nim を `pytra-core` / `pytra-gen` 分離へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-01] 全言語 `sample/01,05` parity（stdout + artifact size + CRC32）を再確認する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-02] backend runtime copy hook / build手順を新レイアウトへ更新する。
- [ ] [ID: P0-IMAGE-RUNTIME-CORE-GEN-01-S4-03] `pytra-core` 画像実装混入禁止チェックを CI/ローカルへ導入する。

決定ログ:
- 2026-03-04: ユーザー指示により、旧 `P0-IMAGE-RUNTIME-SOT-LANG-01` は「間違った実現方式」と判定してTODOから削除。新方式（`pytra-core` / `pytra-gen` 分離）へ再起票した。
- 2026-03-04: `S1-02` 完了。`docs/ja/spec/spec-{codex,dev}.md` と `docs/en/spec/spec-{codex,dev}.md` に `pytra-core` / `pytra-gen` 境界（core直書き禁止、gen生成痕跡必須）を明文化した。
- 2026-03-04: `S2-01` 完了。`tools/gen_image_runtime_from_canonical.py` を追加し、`png.py/gif.py` から14言語の `src/runtime/<lang>/pytra-gen/...` へ出力する共通生成導線を実装。`--targets cpp,cs,js,ts --dry-run` と `test/unit/tooling/test_gen_image_runtime_from_canonical.py` で導線確認。
- 2026-03-04: `S2-02` 完了。`tools/audit_image_runtime_sot.py` を core/gen レイアウト監査へ置換し、`pytra-core` 混入・`pytra-gen` marker不足・legacy配置残存を検知可能化。`work/logs/image_runtime_core_gen_audit_20260304_s2_02.json` で `compliant=1/non_compliant=13` の移行ベースラインを固定。
- 2026-03-04: `S3-RS` 完了。Rust runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.rs` の画像本体を `pytra-gen/utils/image_runtime.rs` へ移設。`backend_registry(_static)` の Rust runtime hook を core+gen コピーへ更新し、`work/logs/runtime_parity_sample_rs_0105_core_gen_split_retry_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-GO` 完了。Go runtime を `pytra-core`/`pytra-gen` へ分離し、画像本体を `pytra-gen/utils/{png.go,gif.go}` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Go 実行導線を `py_runtime.go + png.go + gif.go` に更新し、`work/logs/runtime_parity_sample_go_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-JAVA` 完了。Java runtime を `pytra-core`/`pytra-gen` へ分離し、`PyRuntime.java` の画像本体を `pytra-gen/utils/{PngHelper.java,GifHelper.java}` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Java 実行導線を `PyRuntime + PngHelper + GifHelper` へ更新し、`work/logs/runtime_parity_sample_java_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-SWIFT` 完了。Swift runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.swift` の画像本体（`__pytra_to_u8`〜`__pytra_save_gif`）を `pytra-gen/utils/image_runtime.swift` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Swift 実行導線を `py_runtime + image_runtime` へ更新し、`work/logs/runtime_parity_sample_swift_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-KOTLIN` 完了。Kotlin runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.kt` の画像本体（`__pytra_write_rgb_png`〜`__pytra_save_gif`）を `pytra-gen/utils/image_runtime.kt` へ移設。`backend_registry(_static)` と `runtime_parity_check` の Kotlin 実行導線を `py_runtime + image_runtime` へ更新し、`work/logs/runtime_parity_sample_kotlin_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
- 2026-03-04: `S3-RUBY` 完了。Ruby runtime を `pytra-core`/`pytra-gen` へ分離し、`py_runtime.rb` の画像本体（`__pytra_u16le` 以降）を `pytra-gen/utils/image_runtime.rb` へ移設。`py_runtime.rb` から `require_relative \"image_runtime\"` で読込む導線へ変更し、`backend_registry(_static)` の Ruby runtime hook を core+gen コピーへ更新。`work/logs/runtime_parity_sample_ruby_0105_core_gen_split_20260304.json` で `sample/01,05` parity pass を確認。
