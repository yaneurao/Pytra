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
| rs | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| go | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| java | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| swift | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| kotlin | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| ruby | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| lua | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |
| php | missing | fail/fail | `png.py`/`gif.py` 変換阻害を解消 |

## 分解

- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-01] 全言語の image runtime を自動監査し、marker/probe のベースラインログを固定する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-02] 「画像 writer 手書き禁止（正本由来のみ）」を `docs/ja/spec` / `docs/en/spec` へ明文化する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S1-03] 言語別の着手順（probe ok 群 / probe fail 群）を計画へ確定する。
- [x] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-CPP] C++ を正本準拠の基準実装として再確認し、他言語比較の基準を固定する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-CS] C# image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-JS] JavaScript image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-TS] TypeScript image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-SCALA] Scala3 image helper を正本由来生成へ切替し、`sample/01,05` parity を通す。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S2-NIM] Nim image helper 手書きを撤去し、正本由来生成へ置換して parity を通す。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-RS] Rust の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-GO] Go の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
- [ ] [ID: P0-IMAGE-RUNTIME-SOT-LANG-01-S3-JAVA] Java の `png.py/gif.py` 変換阻害を解消し、正本由来生成へ移行する。
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
