<a href="../../en/plans/p1-nim-sample-parity-complete.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: Nim sample parity 完了化（runtime_parity_check 正式統合）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01`

背景:
- Nim については過去に `sample` parity を通過した記録があるが、現行 `tools/check/runtime_parity_check.py` の `build_targets()` には `nim` target が存在せず、継続的な回帰検証対象から外れている。
- `png/gif` の正本は `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` であり、各言語 runtime へ手書き実装を追加する運用は許可されない。
- 直近で Nim runtime に PNG/GIF 手実装を入れてしまっており、正本運用方針に反しているため是正が必要。
- `tools/gen/regenerate_samples.py` も Nim 未対応のため、`sample/nim` 再生成導線が固定されていない。

目的:
- Nim を `runtime_parity_check` の正式 target として復帰し、`sample` 18件を stdout + artifact（size + CRC32）で全件 pass させる。
- Nim の再生成・検証導線をツール上に固定し、今後の回帰で自動検知できる状態にする。

対象:
- `tools/check/runtime_parity_check.py`（Nim target 追加）
- `tools/gen/regenerate_samples.py`（Nim 対応）
- `src/runtime/nim/pytra/py_runtime.nim`（手実装撤去と正本由来生成への切替）
- `src/pytra/utils/png.py` / `src/pytra/utils/gif.py`（必要最小限の Nim 互換修正）
- `src/toolchain/emit/nim/emitter/nim_native_emitter.py`（runtime 契約接続に必要な範囲）
- `tools/unittest/test_runtime_parity_check_cli.py` / Nim 関連 smoke

非対象:
- Nim backend の性能最適化
- Nim 以外 backend の parity 修正
- README の実行時間表更新

受け入れ基準:
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json` が `case_pass=18` / `case_fail=0`。
- 上記ログで `category_counts` が `ok` のみ（`output_mismatch` / `artifact_*` / `run_failed` / `toolchain_missing` が 0）。
- `python3 tools/gen/regenerate_samples.py --langs nim --force` が成功し、Nim 再生成導線が固定される。
- Nim 追加後も既存 parity CLI テストと Nim transpile/smoke が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/gen/regenerate_samples.py --langs nim --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json`
- `python3 tools/check/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

決定ログ:
- 2026-03-04: ユーザー指示により、Nim parity 完了までの計画を P1 で起票。
- 2026-03-04: `S1-01` を完了。`tools/check/runtime_parity_check.py` の `build_targets()` に `nim` target を追加し、`tools/unittest/tooling/test_runtime_parity_check_cli.py` に Nim エントリ検証を追加。Nim のモジュール名制約（先頭数字不可）対策として parity 実行時は `work/transpile/nim/case_<stem>.nim` へ出力する運用にした。
- 2026-03-04: `S1-02` を完了。`tools/gen/regenerate_samples.py` に `nim` を追加し、`src/toolchain/misc/transpiler_versions.json` へ `languages.nim` を追加。`python3 tools/gen/regenerate_samples.py --langs nim --force` で `summary: total=18 skip=0 regen=18 fail=0` を確認。
- 2026-03-04: `S1-03` を完了。`python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json` を実行し、`case_pass=0/case_fail=18`、カテゴリは `run_failed=16`, `output_mismatch=2` で固定した。
- 2026-03-04: `S2-01` を完了。`src/runtime/nim/pytra/py_runtime.nim` の `write_rgb_png` stub を pure Nim 実装へ置換（CRC32/Adler32/zlib stored block/PNG chunk 組立）。`work/logs/runtime_nim_png_crc_check_20260304.json` で `sample/01` の PNG artifact が `size+crc32` 一致（`artifact_match=true`）を確認。
- 2026-03-04: `S2-02` を完了。Nim runtime に `grayscale_palette` / `save_gif` / GIF向け LZW helper を追加し、`work/logs/runtime_nim_gif_crc_check_20260304.json` で Python 正本と `size+crc32` 一致（`artifact_match=true`）を確認。
- 2026-03-04: 運用是正。`png/gif` は Python 正本からの生成物のみ許可とし、上記 `S2-01/S2-02` の「手実装での完了」は無効化。`S2-01/S2-02` は「手実装撤去＋正本由来差し替え」の未完了タスクとして再オープンした。
- 2026-03-04: `S2-01/S2-02/S2-03/S2-04` を再実装で完了。`nim_native_emitter` に `IfExp/RangeExpr/Unbox/ObjLen/ObjStr/ObjBool/In/NotIn`・tuple target・`enumerate`・bit演算・`range(step)`・クラス自動 ctor / method 前方宣言・`declare` スコープ制御を追加し、`py_runtime.nim` に `py_range`/`py_isdigit`/`py_isalpha` を追加して Python 互換挙動を補完。
- 2026-03-04: `S3-01` を完了。`python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304_after_emitter_fixes.json` で `case_pass=18/case_fail=0`（`ok=18`）を確認。
- 2026-03-04: `S3-02` を完了。`check_py2nim_transpile`・`test_py2nim_smoke`・`test_runtime_parity_check_cli` を再実行して非退行を確認。
- 2026-03-04: `S3-03` を完了。最終ログと修正方針を本計画へ追記し、Nim parity 完了条件を満たした。

## 分解

- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] `runtime_parity_check` に Nim target（transpile/run/toolchain 判定）を追加し、baseline 実行可能な状態にする。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] `regenerate_samples.py` に Nim を追加し、`sample/nim` 再生成導線を固定する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Nim `sample` 全件 parity を実行して失敗カテゴリを固定する（stdout / artifact / run）。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Nim runtime の PNG writer 手実装を撤去し、`src/pytra/utils/png.py` 正本由来の生成物へ置換する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Nim runtime の GIF writer 手実装を撤去し、`src/pytra/utils/gif.py` 正本由来の生成物へ置換する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Nim emitter/lower の画像出力経路と runtime 関数契約（関数名・引数型）を整合させる。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] 失敗が残るケース（例: `sample/18`）の言語機能差分を切り分け、最小修正で解消する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] `--targets nim --all-samples` を再実行し、`case_pass=18` / `case_fail=0` を確認する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Nim parity 契約の回帰テスト（CLI/smoke/transpile）を更新し、再発防止を固定する。
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] 検証ログと運用手順を計画書へ記録し、クローズ条件を明文化する。
