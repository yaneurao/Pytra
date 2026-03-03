# P0: Ruby `sample/18` parity 失敗（tokenize error）原因調査

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUBY-S18-TOKENIZE-INVEST-01`

背景:
- `tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples` で `18_mini_language_interpreter` のみ失敗する。
- 失敗内容は Ruby 実行時の `tokenize error at line=0 pos=6 ch==` で、`run_failed` に分類される。
- parity 検証スクリプトは artifact 事前削除済みであり、今回の failure は stale artifact 起因ではない。

目的:
- Ruby backend で `sample/18` が失敗する根本原因（lower / emitter / runtime / generated code のどこか）を特定する。
- 原因を再現可能な最小ケースへ切り出し、修正方針を確定する。

対象:
- `sample/py/18_mini_language_interpreter.py`
- `sample/ruby/18_mini_language_interpreter.rb`（必要に応じ再生成）
- Ruby backend（lower / emitter）と関連 runtime helper
- parity 失敗ログ（`work/logs/runtime_parity_ruby_sample_after_artifact_purge_20260303.json`）

非対象:
- Ruby backend 全体の最適化
- 他ケース（`01`〜`17`）の速度改善
- README 実行時間表の更新

受け入れ基準:
- 失敗の直接原因をコード位置付きで説明できる（どの変換規則で壊れるかを特定）。
- 最小再現ケース（fixture もしくは sample 断片）を定義できる。
- 修正方針（実装レイヤ、影響範囲、回帰テスト追加箇所）を決定ログへ記録できる。
- 必要なら次段の修正タスクを P0/P1 として分解起票できる。

確認コマンド（予定）:
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter`
- `python3 tools/regenerate_samples.py --langs ruby --stems 18_mini_language_interpreter --force`
- `ruby sample/ruby/18_mini_language_interpreter.rb`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`

決定ログ:
- 2026-03-03: ユーザー指示により、`sample/18` の Ruby parity 失敗（tokenize error）原因調査を P0 として起票。

## 分解

- [ ] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] parity 失敗を再現し、例外発生位置と入力トークン列を採取する。
- [ ] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] Python 版と Ruby 版の tokenize 結果を比較し、最初の乖離点を特定する。
- [ ] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] 乖離を生む変換規則（lower/emitter/runtime）を特定し、責務境界を明確化する。
- [ ] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] 最小再現ケースを `test/fixtures` へ追加する案を作成し、必要な検証粒度を決める。
- [ ] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] 修正方針（実装箇所・非対象・回帰テスト）を確定し、次段修正タスクを起票する。
