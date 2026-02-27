# P0: sample Ruby 実行時間の再計測と README-JA 反映

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SAMPLE-RUBY-BENCH-01`

背景:
- `readme-ja.md` の「実行速度の比較」表は現在 `Kotlin` までで、`Ruby` 列が未掲載。
- `sample/ruby` は `sample/py` 18件の生成物が存在し、各ケースは `elapsed_sec` を出力する実行導線を持つ。
- 既存の比較表は「fresh transpile + warmup/repeat + 中央値」のプロトコルを採用しているため、Ruby 追加も同一条件で揃える必要がある。

目的:
- `sample/py` 18件について Ruby の実行時間を再計測し、`readme-ja.md` の比較表に Ruby 列を右端追加して反映する。

対象:
- `readme-ja.md`
- `sample/ruby/*`（必要時に再生成）
- 計測・検証スクリプト（`tools/` 配下）

非対象:
- `readme.md`（英語版）への反映
- 他言語列の再計測・再更新
- runtime 実装の最適化

受け入れ基準:
- `sample/py` 18件の Ruby 実行時間（中央値）が取得されている。
- `readme-ja.md` の比較表に Ruby 列が右端で追加され、18件すべての値が埋まっている。
- 計測条件（fresh transpile / warmup / repeat / 中央値）が文書化され、再現手順が残っている。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`

決定ログ:
- 2026-02-27: ユーザー要望に基づき、Ruby の sample 実行時間を `readme-ja.md` 比較表へ右端列として追加する `P0-SAMPLE-RUBY-BENCH-01` を起票。

## 分解

- [ ] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-01] 計測プロトコルを固定し、`sample/py` 18件の Ruby 実測値（中央値）を取得する。
- [ ] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-02] `readme-ja.md` の比較表へ Ruby 列（右端）を追加し、18件の値を反映する。
- [ ] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-03] 計測ログ・再現手順・注記同期を完了し、追試可能な状態にする。
