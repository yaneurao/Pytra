# P1: sample/rs/08 出力品質改善（可読性 + ホットパス縮退）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RS-S08-QUALITY-01`

背景:
- `sample/rs/08_langtons_ant.rs` は動作互換は保っているが、生成コードに冗長さが残る。
- とくに次が目立つ。
  - ホットループで負インデックス対応の長い添字正規化式が反復される。
  - `capture` 返却で `clone` が残り、不要コピーの可能性がある。
  - `while + 手動カウンタ` / 入れ子 `if` / `%` 判定多用で可読性と実行効率が低下する。
  - `frames` の容量予約や `println!` 文字列処理が最適化されていない。

目的:
- `sample/rs/08` の生成コード品質を改善し、可読性とホットパス効率を引き上げる。

対象:
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要時）
- `test/unit/test_py2rs_smoke.py`
- `test/unit/test_py2rs_codegen_issues.py`（必要なら新設）
- `sample/rs/08_langtons_ant.rs`（再生成確認）

非対象:
- `sample/08` アルゴリズムの変更
- Rust runtime API の破壊的変更
- Rust backend 全体の一括リファクタ

受け入れ基準:
- `sample/rs/08_langtons_ant.rs` で次の6点が確認できる。
  1. `capture` の `return (frame).clone();` が除去される。
  2. 非負が証明できる添字で、負インデックス正規化式の過剰生成を抑制する。
  3. 単純 `range` 由来ループが `while + 手動カウンタ` から `for` へ縮退する。
  4. `if/elif/elif/else` 由来の深い入れ子分岐が簡素化される。
  5. capture タイミング判定の `%` 連発をカウンタ方式へ置換する。
  6. `frames` へ `reserve` 相当を導入し、再確保を抑制する。
- Rust transpile/smoke/parity が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs rs --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs 08_langtons_ant --ignore-unstable-stdout`

分解:
- [ ] [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長箇所（clone/添字正規化/loop/分岐/capture判定/capacity）をコード断片で固定する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-01] `capture` 返却の不要 `clone` を削減する出力規則を導入する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-02] 非負添字が保証される経路で index 正規化式を省略する fastpath を追加する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-03] 単純 `range` 由来ループを Rust `for` へ縮退する fastpath を追加する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-04] `if/elif` 連鎖を `else if` / `match` 相当へ簡素化する出力規則を追加する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-05] capture 判定 `%` を next-capture カウンタ方式へ置換する fastpath を追加する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-06] 推定可能な `frames` サイズに対する `reserve` 出力規則を追加する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S3-01] 回帰テストを追加し、`sample/rs/08` 再生成差分を固定する。
- [ ] [ID: P1-RS-S08-QUALITY-01-S3-02] transpile/smoke/parity を実行し、非退行を確認する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/rs/08` の出力品質改善を `P1` で計画化し TODO へ追加する方針を確定した。
