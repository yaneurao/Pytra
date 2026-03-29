<a href="../../en/plans/p0-php-image-runtime-and-s16-repair.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: PHP 画像 runtime 実装と sample/16 実行失敗の修復

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PHP-IMAGE-RUNTIME-S16-01`

背景:
- PHP backend は画像出力 helper が no-op で、PNG/GIF artifact を生成しない。
- `sample/php/16_glass_sculpture_chaos.php` は未束縛変数（`$fwd_x/$fwd_y/$fwd_z/$right_*` など）を参照し、`DivisionByZeroError` で停止する。
- parity 検証では、過去 artifact 再利用の可能性を明示的に排除する必要がある。

目的:
- PHP backend で PNG/GIF を実際に書き出せるようにする。
- `sample/16` を PHP で正常実行可能にし、`elapsed_sec` まで到達させる。
- parity 検証時に常に既存 artifact を削除してから実行し、偽陽性を防ぐ。

対象:
- `src/runtime/php/pytra/runtime/png.php`
- `src/runtime/php/pytra/runtime/gif.php`
- PHP backend の画像保存 lower（`__pytra_noop` 経路の撤去）
- PHP backend の tuple/多値返却受け取り lower（`sample/16` の未束縛変数原因）
- `tools/check/runtime_parity_check.py` の artifact クリーンアップ

非対象:
- PHP backend 全体の性能最適化
- 他言語 runtime の同時改修
- README 実行時間表の再更新（別タスクで実施）

受け入れ基準:
- PHP 実行で `sample/01`（PNG）と `sample/06`（GIF）が実際に artifact を生成する。
- `sample/16` が PHP で実行完了し、`output:` と `elapsed_sec:` を出力する。
- parity で `sample` ケース実行前に stale artifact が必ず削除される（コードで担保）。
- `runtime_parity_check --case-root sample --targets php --all-samples` の結果が、少なくとも artifact 偽陽性なしで評価される。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/gen/regenerate_samples.py --langs php --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --all-samples`
- `python3 tools/check/check_py2php_transpile.py`

決定ログ:
- 2026-03-03: ユーザー指示により、PHP 画像 runtime 未実装と `sample/16` 実行失敗を P0 として起票。
- 2026-03-03: parity 偽陽性防止のため、`runtime_parity_check.py` に「毎回 artifact 削除」を明示実装する方針を採用。
- 2026-03-03: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] no-op 依存箇所を棚卸しし、`emitter -> __pytra_noop -> runtime stub(return null)` の経路と `sample/16` の tuple 受け取り崩れ（未束縛変数→`DivisionByZeroError`）を実行再現で確認。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] `src/runtime/php/pytra/runtime/png.php` に pure PHP 実装（CRC32/Adler32/stored-deflate）を追加し、`1x1 RGB` で Python 実装と PNG バイト一致（SHA-256 一致）を確認。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] `src/runtime/php/pytra/runtime/gif.php` に GIF89a 書き出し実装（Clear/Literal LZW・Netscape loop extension）を追加し、`2x1x2frames` で Python 実装と GIF バイト一致（SHA-256 一致）を確認。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] PHP emitter の `save_gif` / `write_rgb_png` を `__pytra_noop` から `__pytra_save_gif` / `__pytra_write_rgb_png` へ切り替え、`sample/01` と `sample/06` の再変換出力および実行で画像生成を確認。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] PHP emitter の `Assign` に tuple/list 展開代入を実装し、`sample/16` の未束縛変数連鎖（`fwd_*`, `right_*`, `dy` など）を解消。再変換後の `sample/16` が `stderr` 空で完走することを確認。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] `runtime_parity_check.py` の `_purge_case_artifacts()` がケース開始時・各ターゲット実行前に必ず呼ばれることを実コードで確認し、artifact 偽陽性防止が常時有効であることを検証。
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] `runtime_parity_check.py` の PHP target から `ignore_artifacts=True` を撤去し、`sample/01,06,16` を `--targets php` で実行して stdout/artifact parity が全件 pass（3/3）することを確認。

## 分解

- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] PHP 画像出力経路（runtime/emit）の no-op 依存箇所を棚卸しする。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] `png.php` に Python 互換の PNG 書き出し実装を追加する。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] `gif.php` に Python 互換の GIF 書き出し実装を追加する。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] PHP emitter/lower の `save_gif` / `write_rgb_png` を `__pytra_noop` から実体 runtime 呼び出しへ切り替える。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] PHP emitter/lower の tuple 受け取りを修正し、`sample/16` の未束縛変数参照を解消する。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] `runtime_parity_check.py` でケース実行前 artifact 削除を強制し、偽陽性経路を閉じる。
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] `sample/01,06,16` を中心に Python vs PHP の stdout/artifact parity を再確認する。

## S1-01 棚卸し結果

- `src/toolchain/emit/php/emitter/php_native_emitter.py`:
  - `save_gif` / `write_rgb_png` 呼び出しを `__pytra_noop(...)` へ強制変換している（関数呼び出し経路と属性呼び出し経路の 2 箇所）。
- `src/runtime/php/pytra/runtime/png.php`:
  - `__pytra_write_rgb_png(...)` は `return null;` のみで実装なし。
- `src/runtime/php/pytra/runtime/gif.php`:
  - `__pytra_save_gif(...)` は `return null;` のみで実装なし。
- `src/runtime/php/pytra/py_runtime.php`:
  - `__pytra_noop(...$_args)` が定義されており、画像保存呼び出しの終着点になっている。
- 生成済み `sample/php`:
  - `sample/php/{01,03,04}` は PNG 出力位置で `__pytra_noop(...)` が出力される。
  - `sample/php/{05..16}` は GIF 出力位置で `__pytra_noop(...)` が出力される。
- `sample/php/16_glass_sculpture_chaos.php` 実行結果:
  - `php sample/php/16_glass_sculpture_chaos.php` で `$fwd_x/$fwd_y/$fwd_z/$right_*` など未束縛変数 warning が連鎖し、最終的に `DivisionByZeroError` で停止。
  - tuple 受け取り lower 崩れが実害として再現することを確認。
