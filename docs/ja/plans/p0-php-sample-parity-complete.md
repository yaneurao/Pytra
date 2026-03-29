<a href="../../en/plans/p0-php-sample-parity-complete.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: PHP sample parity 完了化（stdout + artifact CRC32）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01`

背景:
- 2026-03-04 時点の最新ログ `work/logs/runtime_parity_sample_php_all_after_s13_fix_20260304.json` では、`sample` 18件に対して `case_pass=10`, `case_fail=8`。
- fail はすべて `artifact_crc32_mismatch` で、対象ケースは `05,06,08,10,11,12,14,16`。
- 直前の複合ログ `work/logs/runtime_parity_sample_ruby_lua_scala_php_20260304.json` では PHP の `sample/13` に `stdout mismatch` が残っており、全件完了判定に使える単独 baseline の再固定が必要。
- ユーザー要求として「PHP の sample parity を完了させる」ことが最優先であり、再現・修正・再検証・回帰固定までを 1 タスクで閉じる必要がある。

目的:
- PHP backend で `sample/py` 18件の parity（stdout + artifact size + CRC32）を全件 pass にする。
- fail 要因を runtime / lower / emitter の責務で切り分け、再発しない回帰導線を固定する。

対象:
- `src/runtime/php/pytra/runtime/png.php`
- `src/runtime/php/pytra/runtime/gif.php`
- `src/toolchain/emit/php/lower/**`
- `src/toolchain/emit/php/emitter/**`
- `tools/check/runtime_parity_check.py`
- `tools/unittest/test_runtime_parity_check_cli.py`（必要時）

非対象:
- PHP 実行速度の最適化
- README 実行時間表の更新
- PHP 以外の backend 改修

受け入れ基準:
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_all_pass_20260304.json` で `case_pass=18`, `case_fail=0`。
- 上記ログで `category_counts` が `ok` のみ（`output_mismatch` / `artifact_*` / `run_failed` が 0）。
- 失敗修正に対応する最小回帰（unit または parity 導線）が追加され、同系統の退行を検知できる。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/gen/regenerate_samples.py --langs php --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_rebaseline_20260304.json`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php 05_mandelbrot_zoom 06_julia_parameter_sweep 08_langtons_ant 10_plasma_effect 11_lissajous_particles 12_sorting_visualization 14_simple_raymarching 16_glass_sculpture_chaos --summary-json work/logs/runtime_parity_sample_php_crc_focus_20260304.json`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_all_pass_20260304.json`

決定ログ:
- 2026-03-04: ユーザー指示により、PHP parity 全件完了を P0 で再起票。既存ログ上の未達（`artifact_crc32_mismatch` 8件）を baseline として採用。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-01] `work/logs/runtime_parity_sample_php_rebaseline_20260304_rerun.json` を再生成し、`case_pass=10` / `case_fail=8`（`artifact_crc32_mismatch` のみ）を再確認。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-02] `out/diag_php/05_{py,php}.gif` の先頭差分が byte 804（GCE delay）であることを確認し、`save_gif(delay_cs=..., loop=...)` の keyword が PHP 出力で欠落していると特定。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-03] `src/toolchain/emit/php/emitter/php_native_emitter.py` に `_render_image_runtime_call` を追加し、`save_gif`/`write_rgb_png` の keyword/引数検証と `delay_cs`,`loop` の正規化を実装。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-04] 再検証で残件 `sample/16` のみ不一致となり、GIF先頭差分が byte 13（palette）であることを確認。`palette_332` のビット演算が PHP emitter で `+` に崩れていたため、`BitAnd/BitOr/BitXor/LShift/RShift` を演算子マップへ追加。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-02] `tools/unittest/test_py2php_smoke.py` に `save_gif` keyword 引数順序と `sample/16` ビット演算維持の回帰テストを追加。`python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py'` で 9 件 pass。
- 2026-03-04: [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-01] `work/logs/runtime_parity_sample_php_case16_after_bitops_20260304.json` で `sample/16` 単独 pass を確認後、`work/logs/runtime_parity_sample_php_all_pass_20260304.json` で `case_pass=18` / `case_fail=0` / `category_counts={ok:18}` を達成。

## 分解

- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-01] PHP `sample` 全件 parity を再実行し、単独 target の最新 baseline（失敗ケースとカテゴリ）を固定する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-02] fail 8件（`05,06,08,10,11,12,14,16`）の artifact 差分をケース別に切り分け、`PNG/GIF runtime` と `lower/emitter` のどちらが原因かを分類する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-01] PHP GIF runtime（フレーム順序・LZW・拡張ブロック）を Python 実装準拠へ揃え、GIF 系 CRC mismatch を解消する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-02] PHP PNG runtime（chunk 構築・圧縮経路・CRC 計算）を再検証し、必要な差分を修正する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-03] PHP lower/emitter の画像出力入力（palette/frame/list/bytes 経路）を是正し、runtime へ渡すデータ差分を解消する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-04] `sample/13` の stdout mismatch 再発有無を検証し、未解消なら根本原因を修正する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-01] `--targets php --all-samples` を再実行し、`case_pass=18` / `case_fail=0` を確認する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-02] 修正内容に対応する回帰テスト（unit または parity 用チェック）を追加して再発防止を固定する。
- [x] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-03] 生成ログと決定事項を計画書へ記録し、TODO の完了条件を明示してクローズ可能状態にする。
