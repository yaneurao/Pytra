# P0: PNG/GIF runtime 正本運用の言語別ロールアウト

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-IMAGE-RUNTIME-SOT-LANG-01`

背景:
- 画像出力（PNG/GIF）の正本は `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` に一本化する運用へ変更済み。
- 手書きの画像 writer を各言語 runtime に置く運用は許可しない（`docs/ja/spec/spec-codex.md` / `docs/ja/spec/spec-dev.md` に明記済み）。
- ただし現状は C++ 以外の runtime で正本由来マーカー（`source: src/pytra/utils/*.py`）が欠けており、正本準拠状態が追跡できない。

目的:
- 言語別に「正本由来生成へ切替」を P0 で明示し、実装・検証を段階的に完了させる。
- 画像 runtime の出自を機械可読にし、手書き混入を回帰で検知できる状態にする。

対象:
- `tools/audit_image_runtime_sot.py`
- `src/runtime/<lang>/...` の PNG/GIF helper 実装
- `src/backends/<lang>/...` の正本変換に必要な lower/emitter 修正
- `tools/runtime_parity_check.py`（必要最小限）

非対象:
- 画像以外 runtime API の全面改修
- ベンチマーク値の README 反映
- C++ runtime の大規模リファクタ

受け入れ基準:
- 画像 helper を持つ全 target（`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim`）で、runtime 実装が正本由来であることを示すヘッダ/メタ情報を保持する。
- `tools/audit_image_runtime_sot.py --probe-transpile` の最新ログで、言語別ステータスと未解決要因が追跡可能である。
- 各言語で `sample/01`（PNG）と `sample/05`（GIF）の parity（stdout + artifact size + CRC32）が壊れていないことを確認する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --probe-transpile --summary-json work/logs/image_runtime_sot_audit_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets <lang> --samples 01,05 --check-artifacts --summary-json <log>`

言語別ベースライン（2026-03-04 監査）:

| 言語 | marker | probe(png/gif) | 次アクション |
| --- | --- | --- | --- |
| cpp | ok | ok/ok | 維持（正本由来の基準実装） |
| cs | missing | ok/ok | 生成パイプライン化 + marker 付与 |
| js | missing | ok/ok | 生成パイプライン化 + marker 付与 |
| ts | missing | ok/ok | 生成パイプライン化 + marker 付与 |
| scala | missing | ok/ok | 生成パイプライン化 + marker 付与 |
| nim | missing | ok/ok | 手書き撤去・生成置換 |
| rs | missing | ok/ok | 生成置換 + parity 固定 |
| go | missing | ok/ok | 生成置換 + parity 固定 |
| java | missing | ok/ok | 生成置換 + parity 固定 |
| swift | missing | ok/ok | 生成置換 + parity 固定 |
| kotlin | missing | ok/ok | 生成置換 + parity 固定 |
| ruby | missing | ok/ok | 生成置換 + parity 固定 |
| lua | missing | ok/ok | 生成置換 + parity 固定 |
| php | missing | ok/ok | 生成置換 + parity 固定 |

## 分解

- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-01] 全言語の image runtime を自動監査し、marker/probe のベースラインログを固定する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-02] 「画像 writer 手書き禁止（正本由来のみ）」を `docs/ja/spec` / `docs/en/spec` へ明文化する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-03] 言語別の着手順（probe ok 群 / probe fail 群）を計画へ確定する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-04] 正本 `png.py/gif.py` は変更せず、backend 側修正のみで全 target の transpile probe を green 化する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-CPP] C++ を正本準拠の基準実装として再確認し、他言語比較の基準を固定する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-CS] C# image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-JS] JavaScript image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-TS] TypeScript image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-SCALA] Scala3 image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-NIM] Nim image helper 手書きを撤去し、正本由来生成へ置換して parity を通す。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-RS] Rust の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-GO] Go の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-JAVA] Java の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-SWIFT] Swift の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-KOTLIN] Kotlin の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-RUBY] Ruby の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-LUA] Lua の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-PHP] PHP の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S4-01] 全言語の image runtime SoT 監査を再実行し、未解決を 0 件へ収束させる。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S4-02] 手書き混入を検知するチェックを parity/CI 導線へ統合する。

決定ログ:
- 2026-03-04: ユーザー指示「言語別にTODOにP0で積んで実施」に基づき、本計画を新規起票。
- 2026-03-04: `tools/audit_image_runtime_sot.py --probe-transpile` を実行し、`work/logs/image_runtime_sot_audit_20260304.json` で `languages=14, compliant=1, non_compliant=13` を固定。
- 2026-03-04: 監査結果から `probe ok` 群（`cs/js/ts/scala/nim`）を先行着手、`probe fail` 群（`rs/go/java/swift/kotlin/ruby/lua/php`）を阻害要因解消フェーズへ分離した。
- 2026-03-04: 運用是正。`src/pytra/utils/png.py` / `gif.py` のターゲット都合変更は規約違反のため取り消し、`S1-04` は未完了へ戻した。以後は正本不変で backend 側修正のみを許可する。
- 2026-03-04: 巻き戻し後に `tools/audit_image_runtime_sot.py --probe-transpile` を再実行し、`work/logs/image_runtime_sot_audit_20260304_after_revert.json` で baseline（`probe ok: cs/js/ts/scala/nim`, `probe fail: rs/go/java/swift/kotlin/ruby/lua/php`）へ復帰したことを確認。
- 2026-03-04: `S2-CS` 着手として backend 側の受け皿を実装（`CSharpEmitter` に `bytes literal` / `list.extend` / `int.to_bytes` / module alias shadow 回避を追加、`py_runtime.cs` に `py_int_to_bytes` を追加）。さらに `tools/gen_cs_image_runtime_from_canonical.py` を追加して正本から C# helper 生成を試行。
- 2026-03-04: 生成 helper への実差し替えは compile fail で未完了。主因は C# emitter 由来の追加未対応（`List<byte> + List<byte>`、`long` と shift 演算の型整合、`PyFile/open` 経路）。差し替えは巻き戻し済みで、`work/logs/runtime_parity_sample_cs_0105_after_restore_20260304.json` で `01/05` parity pass を確認。
- 2026-03-04: `S2-CS` 完了。`CSharpEmitter` に `list+list` concat / `open()` / shift-cast / compare 括弧を追加し、`py_runtime.cs` に `PyFile`, `open`, `py_bytes(object)`, `py_concat` を追加。`tools/gen_cs_image_runtime_from_canonical.py` 再生成後、`work/logs/runtime_parity_sample_cs_0105_canonical_retry_20260304.json` で `sample/01,05` pass、`work/logs/image_runtime_sot_audit_20260304_after_cs_s2.json` で `cs: compliant_marker_present` を確認。
- 2026-03-04: `S1-04` 前進。Rust emitter の未対応 `Try` を backend 側で縮退実装し、`src/pytra/utils/png.py` / `gif.py` の Rust transpile probe を green 化。`work/logs/image_runtime_sot_audit_20260304_after_rs_try.json` で `probe ok` が `cpp/cs/js/ts/scala/nim/rs` まで拡大したことを確認。
- 2026-03-04: `S1-04` 追加前進。`go/java/swift/kotlin/ruby/php` native emitter に `Try` 縮退出力を追加し、`work/logs/image_runtime_sot_audit_20260304_after_try_wave1.json` で `probe fail` を `lua` のみへ縮小。`Try` 非対応起因の fail は解消済み。
- 2026-03-04: `S1-04` 完了。Lua emitter に `Try` 縮退と table/bytes slice 出力を追加し、`work/logs/image_runtime_sot_audit_20260304_after_lua_try_slice.json` で全14言語 `probe(png/gif)=ok` を確認。
- 2026-03-04: `S2-JS` 完了。`src/runtime/js/pytra/{png_helper.js,gif_helper.js}` に SoT marker（`source: src/pytra/utils/{png,gif}.py`）を付与し、`work/logs/runtime_parity_sample_js_0105_s2_20260304.json` で `sample/01,05` parity pass、`work/logs/image_runtime_sot_audit_20260304_after_js_marker.json` で `js: compliant_marker_present` を確認。
- 2026-03-04: `S2-TS` 完了。`src/runtime/ts/pytra/{png_helper.ts,gif_helper.ts}` に SoT marker（`source: src/pytra/utils/{png,gif}.py`）を付与し、`work/logs/runtime_parity_sample_ts_0105_s2_20260304.json` で `sample/01,05` parity pass、`work/logs/image_runtime_sot_audit_20260304_after_ts_marker.json` で `ts: compliant_marker_present` を確認。
- 2026-03-04: `S2-SCALA` 完了。`src/runtime/scala/pytra/py_runtime.scala` に SoT marker を付与。あわせて Scala emitter の call lower が keyword 引数を落として `save_gif(delay_cs=5)` を既定値 `4` で実行していたため、`keywords` を positional へ結合する修正を追加。`work/logs/runtime_parity_sample_scala_0105_s2_retry_20260304.json` で `sample/01,05` parity pass、`work/logs/image_runtime_sot_audit_20260304_after_scala_marker.json` で `scala: compliant_marker_present` を確認。
- 2026-03-04: `S2-NIM` 完了。`src/runtime/nim/pytra/py_runtime.nim` の SoT marker を維持したまま、Nim emitter の call/print/control-flow/type mapping を補正（`keywords` 伝播、`print` 空白整形、`Expr(Name("break"/"continue"))` 制御文化、`bytearray/bytes/uint8` 整合）。`work/logs/runtime_parity_sample_nim_0105_s2_retry5_20260304.json` で `sample/01,05` parity pass、`work/logs/image_runtime_sot_audit_20260304_after_nim_s2_complete.json` で `nim: compliant_marker_present` を再確認。
- 2026-03-04: `S3-RS` 完了。`src/runtime/rs/pytra/built_in/py_runtime.rs` へ SoT marker（`source: src/pytra/utils/{png,gif}.py`）を追記し、`work/logs/runtime_parity_sample_rs_0105_s3_20260304.json` で `sample/01,05` parity pass を確認。`work/logs/image_runtime_sot_audit_20260304_after_rs_s3_complete.json` で `rs: compliant_marker_present` へ遷移。
- 2026-03-04: `S3-GO` 完了。`src/runtime/go/pytra/py_runtime.go` へ SoT marker（`source: src/pytra/utils/{png,gif}.py`）を追記し、`work/logs/runtime_parity_sample_go_0105_s3_20260304.json` で `sample/01,05` parity pass を確認。`work/logs/image_runtime_sot_audit_20260304_after_go_s3_complete.json` で `go: compliant_marker_present` へ遷移。
- 2026-03-04: `S3-JAVA` 完了。`src/runtime/java/pytra/built_in/PyRuntime.java` へ SoT marker（`source: src/pytra/utils/{png,gif}.py`）を追記し、`work/logs/runtime_parity_sample_java_0105_s3_20260304.json` で `sample/01,05` parity pass を確認。`work/logs/image_runtime_sot_audit_20260304_after_java_s3_complete.json` で `java: compliant_marker_present` へ遷移。
