# P0: Ruby `/` 演算の真の除算互換修正

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-RUBY-DIV-SEMANTICS-01`

背景:
- Ruby backend 生成コードで `int / int` が Ruby の整数除算として評価され、Python の `/`（真の除算）と意味差が発生している。
- この差分により `sample/06_julia_parameter_sweep` など浮動小数座標計算を含むケースで挙動が変わり、parity と実行時間比較の妥当性が崩れる。

目的:
- Ruby backend における `/` の意味を Python 互換（常に true division）へ揃え、少なくとも `sample/06` を含む既知ケースで意味差を解消する。

対象:
- Ruby emitter の二項演算 lower（`/`）
- Ruby 向けユニット/スモーク回帰
- `sample/ruby` 再生成と parity 確認手順

非対象:
- `//`（floor division）や `%` の仕様拡張
- Ruby 全体最適化（性能チューニング）
- 他言語 backend の除算仕様変更

受け入れ基準:
- Ruby 生成コードで Python の `/` が true division として評価される。
- `sample/06` を含む回帰ケースで Ruby 実行結果が Python と一致する（不安定行除外の既存判定に従う）。
- `/` 意味差を再発防止するテスト（unit または smoke）が追加され、CI 導線で検知可能になる。

確認コマンド:
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-27: `sample/05` 遅延要因分析の過程で `sample/06` Ruby 生成コードの `int/int` 除算意味差を確認。P0 として修正タスクを起票。

## 分解

- [ ] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-01] `sample/06` を含む再現ケースを固定化し、`/` 意味差を検知する回帰テストを追加する。
- [ ] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-02] Ruby emitter の `/` lower を true division 準拠へ修正し、既存変換との互換性を確認する。
- [ ] [ID: P0-RUBY-DIV-SEMANTICS-01-S1-03] `sample/ruby` を再生成し、runtime parity と README 計測再実施時の確認手順を更新する。
