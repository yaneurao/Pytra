<a href="../../en/plans/p0-php-s13-parity-investigation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample/13 PHP parity 不一致（frames 147→2）原因調査

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PHP-S13-PARITY-INVEST-01`

背景:
- `tools/runtime_parity_check.py --case-root sample --all-samples --targets ruby,lua,scala,php` の最新実行で、失敗は `sample/13` の PHP 1件のみ。
- 失敗内容は stdout 不一致で、Python 期待値 `frames: 147` に対し PHP 実測値が `frames: 2`。
- `sample/16` / `sample/18` の PHP 実行は通るため、PHP backend 全面障害ではなく `sample/13` 固有の変換経路不整合の可能性が高い。

目的:
- `sample/13` の PHP 出力が `frames: 2` になる根本原因を特定する。
- 原因の層（EAST3 / lower / emitter / runtime / sample 側）を切り分ける。
- 修正実装に進むための最小再現ケースと対処方針を確定する。

対象:
- `sample/py/13_maze_generation_steps.py`
- `sample/php/13_maze_generation_steps.php`（必要なら再生成）
- PHP backend（lower / emitter）
- PHP runtime（GIF 出力・配列処理・ループ関連 helper）
- parity ログ（`work/logs/runtime_parity_sample_ruby_lua_scala_php_20260304.json`）

非対象:
- 4言語全体の parity 再設計
- PHP の性能最適化
- README 実行時間表の更新

受け入れ基準:
- `frames: 147 -> 2` に至る直接原因を、コード位置付きで説明できる。
- Python 実装との最初の乖離点を示せる（データ/制御のどちらか）。
- 最小再現ケース案を確定できる。
- 次段修正タスク（実装ID）を切れる状態まで調査結果を整理できる。

確認コマンド（予定）:
- `python3 tools/runtime_parity_check.py --case-root sample --targets php 13_maze_generation_steps`
- `python3 tools/regenerate_samples.py --langs php --stems 13_maze_generation_steps --force`
- `php sample/php/13_maze_generation_steps.php`
- `python3 sample/py/13_maze_generation_steps.py`

決定ログ:
- 2026-03-04: ユーザー指示により、`sample/13` PHP parity 失敗（`frames: 147 -> 2`）の原因調査を P0 で起票。
- 2026-03-04: `python3 tools/runtime_parity_check.py --case-root sample --targets php 13_maze_generation_steps` で `output mismatch (frames: 147 -> 2)` を再現し、失敗ログを `work/logs/runtime_parity_sample_php_13_invest_20260304.json` に固定。
- 2026-03-04: 生成PHPを比較し、最初の乖離点を `stack[-1]` の負インデックス未対応（`$stack[-1]` 直出力）と特定。PHP実行時に `Undefined array key -1` が発生し、探索が即枯渇して `frames: 2` になることを確認。
- 2026-03-04: 併発要因として `ListComp` 未対応（`_render_expr` fallback `null`）も確認。最小再現 `/tmp/php_s13_min_repro.py` では `grid = [[1] * w for _ in range(h)]` が `$grid = null` に落ちることを確認。
- 2026-03-04: 修正方針を即時実装へ転換し、PHP emitter に `AnnAssign/Assign` の `ListComp(range)` 展開を追加、`BinOp Mult` に list repeat 経路（`__pytra_list_repeat`）を追加、runtime に `__pytra_index` / `__pytra_list_repeat` を追加。
- 2026-03-04: `sample/13` の parity は `php` 単独で `ok`（`work/logs/runtime_parity_sample_php_13_after_negindex_fix_20260304.json`）、`ruby,lua,scala,php` 横並びでも `ok`（`work/logs/runtime_parity_sample_ruby_lua_scala_php_case13_after_php_fix_20260304.json`）を確認。次段修正タスクの別起票は不要（本ID内で修正実施）。

## 分解

- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-01] parity 失敗（stdout mismatch）を単独再現し、実行ログと生成 artifact の最小情報を採取する。
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-02] Python と PHP の `frames` 算出経路を比較し、最初の乖離点を特定する。
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-01] 乖離を生む層（EAST3 / lower / emitter / runtime）を 1 箇所に特定する。
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-02] 最小再現ケース案を作成し、回帰テストへ落とし込む粒度を決める。
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S3-01] 修正方針（実装箇所・非対象・検証観点）を確定し、次段の修正タスクを起票する。
