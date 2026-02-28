# P1: Ruby benchmark 再計測と README 反映是正

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUBY-BENCH-FIX-01`

背景:
- `docs/ja/README.md` の実行速度比較表にある Ruby 値が、実測条件と一致しないケース（`sample/01`）が発生した。
- 既存運用では「再計測 → parity 確認 → README 反映」の順序が明文化不足で、古い値が残るリスクがある。

目的:
- Ruby 計測値の更新手順を固定し、README 反映時に parity 未確認の値が入らないようにする。

対象:
- `sample/ruby/*`（fresh 生成）
- `tools/runtime_parity_check.py`（既存手順の利用）
- `docs/ja/README.md`（比較表）

非対象:
- C++/Rust など他言語の再計測
- Ruby runtime 実装の最適化

受け入れ基準:
- `sample/01` の Ruby 実測（`ruby --yjit`, `warmup=1`, `repeat=5`, 中央値）をログ化できる。
- Ruby parity を再確認したうえで、`docs/ja/README.md` の Ruby 列へ実測値を反映できる。
- 作業ログ（計測ログ/確認コマンド）が `work/logs` と文脈ファイルで追跡できる。

確認コマンド（予定）:
- `python3 tools/regenerate_samples.py --langs ruby --stems 01_mandelbrot --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot --ignore-unstable-stdout`
- `ruby --yjit sample/ruby/01_mandelbrot.rb`

## 分解

- [ ] [ID: P1-RUBY-BENCH-FIX-01] Ruby 計測値更新時に「fresh transpile → parity確認 → README反映」を必須化する。
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-01] `sample/01` を `ruby --yjit`（`warmup=1`, `repeat=5`）で再計測し、ログを保存する。
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-02] `runtime_parity_check` で `sample/01` の Ruby parity を確認する。
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-03] `docs/ja/README.md` の Ruby 列へ測定値を反映し、差分を確定する。

決定ログ:
- 2026-03-01: ユーザー指示により、Ruby 計測値反映ミス再発防止のため `P1-RUBY-BENCH-FIX-01` を起票した。
- 2026-03-01: `python3 tools/regenerate_samples.py --langs ruby --stems 01_mandelbrot --force` を実行し、fresh 生成（`summary: total=1 regen=1 fail=0`）を確認した。
- 2026-03-01: `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot --ignore-unstable-stdout` で `SUMMARY cases=1 pass=1 fail=0` を確認した（`S1-02`）。
- 2026-03-01: `ruby --yjit` の `warmup=1` / `repeat=5` 計測を実施し、`work/logs/bench_ruby_yjit_01_mandelbrot_20260301.json` へ保存した。中央値は `18.954643653007224` 秒（`S1-01`）。
- 2026-03-01: `docs/ja/README.md` の `01_mandelbrot` Ruby 列を `18.682 -> 18.955` へ更新した（`S1-03`）。
