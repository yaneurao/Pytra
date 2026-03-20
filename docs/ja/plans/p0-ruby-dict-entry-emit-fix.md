# P0: Ruby Dict literal（EAST3 `entries`）emit 修正

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01`

背景:
- `P0-RUBY-S18-TOKENIZE-INVEST-01` で、`sample/18` Ruby 失敗の直接原因が判明した。
- EAST3 の `Dict` ノードは `entries` 配列を持つが、`src/toolchain/emit/ruby/emitter/ruby_native_emitter.py` の `_render_dict_expr` は旧 `keys/values` 形式のみを参照している。
- その結果、`single_char_token_tags: dict[str, int] = {...}` が Ruby 生成コードでは `{}` になり、`=` トークン判定が壊れて `tokenize error at line=0 pos=6 ch==` で停止する。

目的:
- Ruby emitter の dict literal 生成を EAST3 `entries` に正しく追従させる。
- `sample/18` の Ruby parity 失敗を解消する。

対象:
- `src/toolchain/emit/ruby/emitter/ruby_native_emitter.py`
- `test/fixtures` または `test/unit` の Ruby 回帰ケース（dict literal）
- `tools/runtime_parity_check.py` を使った `sample/18` Ruby 再検証

非対象:
- Ruby backend 全体最適化
- `sample/18` 以外の性能改善
- 他言語 emitter の同時改修

受け入れ基準:
- Ruby emitter が EAST3 `Dict(entries=...)` を正しく `{ k => v, ... }` へ出力する。
- dict literal 最小再現ケースで Ruby 出力が `{}` へ崩れないことをテストで検出できる。
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter` が pass する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_smoke.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter`

決定ログ:
- 2026-03-04: `P0-RUBY-S18-TOKENIZE-INVEST-01` の後続実装として起票。修正焦点は `_render_dict_expr` の `entries` 対応に限定する。
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-01] `_render_dict_expr` を `entries` 優先に改修し、旧 `keys/values` 形式をフォールバック対応。`sample/18` 生成コードで `single_char_token_tags = { "+" => 1, ... "=" => 7 }` が復元されることを確認。
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-02] `test/fixtures/core/dict_literal_entries.py` と `test_py2rb_smoke.py` の回帰テストを追加し、dict literal が `{}` へ崩れないことを検証可能化。
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S2-01] `runtime_parity_check --case-root sample --targets ruby 18_mini_language_interpreter` を再実行し pass（1/1）を確認。`check_py2rb_transpile`（133/133）と `test_py2rb_smoke`（25 tests）も非退行を確認。

## 分解

- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-01] `_render_dict_expr` を `entries` 優先でレンダリングし、旧 `keys/values` も後方互換で扱う。
- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-02] dict literal 最小再現 fixture と Ruby 変換回帰テストを追加する。
- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S2-01] `sample/18` Ruby parity を再実行し、失敗解消を確認する。
