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
- `python3 tools/regenerate_samples.py --langs js,ts,ruby,lua,java --stems 01_mandelbrot,18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets js,ts,ruby,lua,java --ignore-unstable-stdout 01_mandelbrot 18_mini_language_interpreter`

分解:
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] 各言語の冗長構文パターン（不要括弧/補助変数/append連鎖）を棚卸しし、適用境界を定義する。
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] `js/ts` の loop 補助変数（`__start_N`）を簡約する出力規則を実装する。
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] `ruby/lua` の append 連鎖を簡約する出力規則を実装する。
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] `java` の冗長括弧/step 変数の簡約規則を実装する。
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] 回帰テストを追加して可読性退行を検知可能にする。
- [ ] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] 対象 sample を再生成し、transpile/parity で非退行を確認する。

決定ログ:
- 2026-03-02: sample 多言語品質調査の「可読性のみ改善」項目を P2 として分離し、正しさ修正（P0）と混線しない実施順を確定した。
