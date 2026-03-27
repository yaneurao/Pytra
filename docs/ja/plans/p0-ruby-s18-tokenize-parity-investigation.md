<a href="../../en/plans/p0-ruby-s18-tokenize-parity-investigation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: Ruby `sample/18` parity 失敗（tokenize error）原因調査

最終更新: 2026-03-04

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
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] `runtime_parity_check --case-root sample --targets ruby 18_mini_language_interpreter` と `ruby out/ruby_validate/18_mini_language_interpreter.rb` の双方で `tokenize error at line=0 pos=6 ch==` を再現。入力先頭行は `let a = 10` で、生成 Ruby では `single_char_token_tags = {}`（`=` の辞書登録欠落）になっていることを確認。
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] 同一入力 `let a = 10` で Python tokenize は `LET, IDENT, EQUAL, NUMBER...` を返す一方、Ruby 版は `pos=6 ('=')` で停止。最初の乖離点は `single_char_token_tags` 初期化（Python: `{'=':7,...}` / Ruby生成: `{}`）で確定。
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] 乖離を生む規則は Ruby emitter 側 `Dict` レンダリングと特定。EAST3 の `Dict` は `entries` 配列だが、`ruby_native_emitter._render_dict_expr` は旧 `keys/values` 形式のみを参照して `{}` を返していた。
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] 最小再現ケースは「型注釈付き dict literal を初期化して `.get()` で参照」方針で十分と判断（`d: dict[str, int] = {"=": 7}; print(d.get("=", 0))`）。`tokenize` 全体ではなく dict literal 経路単体の fixture 化を採用。
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] 修正方針を `Ruby emitter Dict(entries) 対応 + fixture 回帰 + sample/18 parity 再確認` に確定し、実装タスク P0-RUBY-DICT-ENTRY-EMIT-FIX-01 を TODO に起票。

## 分解

- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] parity 失敗を再現し、例外発生位置と入力トークン列を採取する。
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] Python 版と Ruby 版の tokenize 結果を比較し、最初の乖離点を特定する。
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] 乖離を生む変換規則（lower/emitter/runtime）を特定し、責務境界を明確化する。
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] 最小再現ケースを `test/fixtures` へ追加する案を作成し、必要な検証粒度を決める。
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] 修正方針（実装箇所・非対象・回帰テスト）を確定し、次段修正タスクを起票する。
