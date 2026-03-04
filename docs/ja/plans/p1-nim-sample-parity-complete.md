# P1: Nim sample parity 完了化（runtime_parity_check 正式統合）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01`

背景:
- Nim については過去に `sample` parity を通過した記録があるが、現行 `tools/runtime_parity_check.py` の `build_targets()` には `nim` target が存在せず、継続的な回帰検証対象から外れている。
- `src/runtime/nim/pytra/py_runtime.nim` は最小実装で、`write_rgb_png` が stub のまま、`save_gif` も未実装であり、artifact 生成ケース（PNG/GIF）を CRC32 まで一致させるには不足がある。
- `tools/regenerate_samples.py` も Nim 未対応のため、`sample/nim` 再生成導線が固定されていない。

目的:
- Nim を `runtime_parity_check` の正式 target として復帰し、`sample` 18件を stdout + artifact（size + CRC32）で全件 pass させる。
- Nim の再生成・検証導線をツール上に固定し、今後の回帰で自動検知できる状態にする。

対象:
- `tools/runtime_parity_check.py`（Nim target 追加）
- `tools/regenerate_samples.py`（Nim 対応）
- `src/runtime/nim/pytra/py_runtime.nim`（PNG/GIF 等の不足 runtime 実装）
- `src/backends/nim/emitter/nim_native_emitter.py`（runtime 契約接続に必要な範囲）
- `test/unit/test_runtime_parity_check_cli.py` / Nim 関連 smoke

非対象:
- Nim backend の性能最適化
- Nim 以外 backend の parity 修正
- README の実行時間表更新

受け入れ基準:
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json` が `case_pass=18` / `case_fail=0`。
- 上記ログで `category_counts` が `ok` のみ（`output_mismatch` / `artifact_*` / `run_failed` / `toolchain_missing` が 0）。
- `python3 tools/regenerate_samples.py --langs nim --force` が成功し、Nim 再生成導線が固定される。
- Nim 追加後も既存 parity CLI テストと Nim transpile/smoke が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs nim --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json`
- `python3 tools/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

決定ログ:
- 2026-03-04: ユーザー指示により、Nim parity 完了までの計画を P1 で起票。
- 2026-03-04: `S1-01` を完了。`tools/runtime_parity_check.py` の `build_targets()` に `nim` target を追加し、`test/unit/tooling/test_runtime_parity_check_cli.py` に Nim エントリ検証を追加。Nim のモジュール名制約（先頭数字不可）対策として parity 実行時は `test/transpile/nim/case_<stem>.nim` へ出力する運用にした。
- 2026-03-04: `S1-02` を完了。`tools/regenerate_samples.py` に `nim` を追加し、`src/toolchain/compiler/transpiler_versions.json` へ `languages.nim` を追加。`python3 tools/regenerate_samples.py --langs nim --force` で `summary: total=18 skip=0 regen=18 fail=0` を確認。
- 2026-03-04: `S1-03` を完了。`python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json` を実行し、`case_pass=0/case_fail=18`、カテゴリは `run_failed=16`, `output_mismatch=2` で固定した。
- 2026-03-04: `S2-01` を完了。`src/runtime/nim/pytra/py_runtime.nim` の `write_rgb_png` stub を pure Nim 実装へ置換（CRC32/Adler32/zlib stored block/PNG chunk 組立）。`work/logs/runtime_nim_png_crc_check_20260304.json` で `sample/01` の PNG artifact が `size+crc32` 一致（`artifact_match=true`）を確認。

## 分解

- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] `runtime_parity_check` に Nim target（transpile/run/toolchain 判定）を追加し、baseline 実行可能な状態にする。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] `regenerate_samples.py` に Nim を追加し、`sample/nim` 再生成導線を固定する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Nim `sample` 全件 parity を実行して失敗カテゴリを固定する（stdout / artifact / run）。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Nim runtime の PNG writer を Python 準拠バイナリ（size+CRC32一致）へ実装する。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Nim runtime の GIF writer（`grayscale_palette` 含む）を実装し、GIF artifact mismatch を解消する。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Nim emitter/lower の画像出力経路と runtime 関数契約（関数名・引数型）を整合させる。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] 失敗が残るケース（例: `sample/18`）の言語機能差分を切り分け、最小修正で解消する。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] `--targets nim --all-samples` を再実行し、`case_pass=18` / `case_fail=0` を確認する。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Nim parity 契約の回帰テスト（CLI/smoke/transpile）を更新し、再発防止を固定する。
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] 検証ログと運用手順を計画書へ記録し、クローズ条件を明文化する。
