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

## 分解

- [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-01] parity 失敗（stdout mismatch）を単独再現し、実行ログと生成 artifact の最小情報を採取する。
- [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-02] Python と PHP の `frames` 算出経路を比較し、最初の乖離点を特定する。
- [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-01] 乖離を生む層（EAST3 / lower / emitter / runtime）を 1 箇所に特定する。
- [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-02] 最小再現ケース案を作成し、回帰テストへ落とし込む粒度を決める。
- [ ] [ID: P0-PHP-S13-PARITY-INVEST-01-S3-01] 修正方針（実装箇所・非対象・検証観点）を確定し、次段の修正タスクを起票する。
