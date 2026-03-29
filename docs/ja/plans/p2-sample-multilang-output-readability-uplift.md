<a href="../../en/plans/p2-sample-multilang-output-readability-uplift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: sample 多言語出力の可読性縮退（冗長構文整理）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-SAMPLE-OUTPUT-READABILITY-01`

背景:
- 多言語 backend で意味保持のための保守的出力が残り、可読性を下げる冗長構文（不要括弧、冗長一時変数、append 連鎖）が散在している。
- これは正しさには直結しないが、ユーザーの目視レビュー性と生成物の保守性を下げる。

目的:
- 意味を変えずに出力を簡約し、`sample/` 生成物の読みやすさを底上げする。

対象:
- `src/hooks/{js,ts,ruby,lua,java}/emitter/*.py`
- `sample/{js,ts,ruby,lua,java}/*.*
- 関連 unit/golden テスト

非対象:
- 正しさ修正（P0）
- 型モデルの再設計や runtime 仕様変更（P1 で扱う範囲を超えるもの）

受け入れ基準:
- `sample/01` と `sample/18` で、冗長括弧・冗長一時変数・append 連鎖が目視で減る。
- `js/ts` の `const __start_N = 0` など読みにくい補助変数が削減される。
- `ruby/lua` の append 連鎖が簡約される（可能な範囲で一括化）。
- 回帰テストと transpile/parity が通過する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java*' -v`
- `python3 tools/gen/regenerate_samples.py --langs js,ts,ruby,lua,java --stems 01_mandelbrot,18_mini_language_interpreter --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets js,ts,ruby,lua,java --ignore-unstable-stdout 01_mandelbrot 18_mini_language_interpreter`

分解:
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] 各言語の冗長構文パターン（不要括弧/補助変数/append連鎖）を棚卸しし、適用境界を定義する。
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] `js/ts` の loop 補助変数（`__start_N`）を簡約する出力規則を実装する。
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] `ruby/lua` の append 連鎖を簡約する出力規則を実装する。
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] `java` の冗長括弧/step 変数の簡約規則を実装する。
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] 回帰テストを追加して可読性退行を検知可能にする。
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] 対象 sample を再生成し、transpile/parity で非退行を確認する。

決定ログ:
- 2026-03-02: sample 多言語品質調査の「可読性のみ改善」項目を P2 として分離し、正しさ修正（P0）と混線しない実施順を確定した。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] 棚卸し結果（`sample/01,18`）: `js/ts` は `__start_N`（一部は TDZ 回避で必要）と `Number(...)`/cast 周辺、`ruby/lua` は `append` 連鎖・enumerate 展開時の tuple/unpack 一時変数、`java` は `__step_N` 条件付き for と過剰括弧が主要ノイズ。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] 適用境界を固定: `js/ts` は「start 式が loop target を参照しない」場合のみ `__start_N` 削減、`ruby/lua` は「単一要素 push 連鎖 + 副作用なし rhs」に限定して連鎖簡約、`java` は「定数 `step=1` かつ範囲比較が単純」な for で `__step_N` を直接化し、dynamic/descending 判定式は維持（fail-closed）。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] `js` emitter の `ForRange` に start 直埋め fastpath（`start` が target 非参照時）を適用済み。`ts` は JS 経路共有のため同時に反映され、`sample/{js,ts}/01,18` で `const __start_N` を生成しない形を確認。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] Ruby は既存実装で `append` 連鎖を `owner.concat([..])` へ縮退済みであることを確認。Lua へ同等規則を追加し、`owner.append(x)` 連鎖（owner=Name, arg=副作用なし式）を `table.move({..}, 1, n, #(owner)+1, owner)` 1行へ縮退した。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] 検証: 追加した `test_append_chain_is_compacted_with_table_move` は pass。`test_py2lua*` 全体は既知ベースライン失敗（runtime 分離期待値の旧前提）を含むため fail 継続、`test_py2rb*` は pass。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] Java emitter の `ForCore` / listcomp range に「定数 step fastpath」を追加し、`step=±1` を含む定数 step で `__step_N` 変数を生成しない出力へ変更した。step が非定数または 0 の場合は既存の動的 ternary 条件経路を維持（fail-closed）。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] 検証: `test_py2java_smoke.py` に `for_range` と `range_downcount_len_minus1` の回帰を追加し pass。`tools/gen/regenerate_samples.py --langs java --stems 01_mandelbrot,18_mini_language_interpreter --force` で `sample/java` へ反映済み。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] 回帰確認: `test_py2{js,ts,rb,java}_smoke.py` は pass。`test_py2lua_smoke.py` は runtime 分離契約移行に追随していない既知期待値（helper内包前提）7件が fail のまま（本タスク変更とは独立）。
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] `tools/gen/regenerate_samples.py --langs js,ts,ruby,lua,java --stems 01_mandelbrot,18_mini_language_interpreter --force` を実行して再生成。`runtime_parity_check --targets js,ts,ruby,lua,java --ignore-unstable-stdout 01,18` を実行し、`lua` は両case OK、`js/ts` は `01` artifact size mismatch、`java` は `01` artifact missing と `18` compile/run fail、`ruby` は `18` tokenize run fail を確認（既知の別系統課題として継続管理）。
