<a href="../../en/plans/p0-sample-multilang-output-correctness-fixes.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample 多言語出力の正しさ修正（Scala/C#）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01`

背景:
- `sample/` の生成コード横断確認で、見た目の冗長性だけでなく正しさに影響し得る出力が確認された。
- Scala では演算子優先順位を壊す式が混入し、Python 原式と異なる計算順になる箇所がある（例: `255.0 * (1.0 - t)` が `255.0 * 1.0 - t` になる）。
- C# では typed 経路で `double t = iter_count / max_iter;` のような整数除算経由の式があり、将来的な再利用時に誤差を埋め込む。

目的:
- sample 生成物のうち「意味差分を生む/生み得る」出力を先に是正し、以降の品質改善を安全に進める土台を作る。

対象:
- `src/hooks/scala/emitter/*.py`
- `src/hooks/cs/emitter/*.py`
- `sample/scala/01_mandelbrot.scala`
- `sample/cs/01_mandelbrot.cs`
- 関連 unit/golden テスト

非対象:
- 速度最適化（hot path 最適化は P1 で扱う）
- 可読性のみの調整（冗長括弧/一時変数削減は P2 で扱う）

受け入れ基準:
- Scala 出力で `sample/01` の数式が Python と同値な優先順位で出力される。
- C# 出力で typed 数値除算が浮動小数経路で行われ、整数除算依存が除去される。
- 追加回帰テストで同種の式崩れ（Scala）と typed 除算退行（C#）を検知可能になる。
- `sample/01` の Scala/C# parity が通過する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs*' -v`
- `python3 tools/gen/regenerate_samples.py --langs scala,cs --stems 01_mandelbrot --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets scala,cs --ignore-unstable-stdout 01_mandelbrot`

分解:
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-01] Scala emitter で算術式の優先順位保持を修正し、`sample/scala/01` の崩れ式を解消する。
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-02] C# emitter の typed 除算出力を修正し、整数除算経路を除去する。
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-01] Scala/C# の回帰テストを追加し、同種退行を固定する。
- [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-02] `sample/01` 再生成 + parity で非退行を確認する。

決定ログ:
- 2026-03-02: sample 多言語コード品質調査で、正しさ影響ありの修正（Scala 優先順位/C# 除算）を P0 として分離した。
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-01] `scala_native_emitter.py` に binop precedence 判定（`_binop_precedence` / `_wrap_binop_operand`）を導入し、`255.0 * (1.0 - t)` の括弧を保持するよう修正。
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-02] `cs_emitter.py` の `Div` 出力を `System.Convert.ToDouble(lhs) / System.Convert.ToDouble(rhs)` に統一し、typed 経路での整数除算を排除。
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-01] `test_py2scala_smoke.py` / `test_py2cs_smoke.py` に回帰テストを追加し、式優先順位崩れと typed 除算退行を固定。
- 2026-03-02: [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-02] `regenerate_samples` で `sample/{scala,cs}/01_mandelbrot` を再生成し、`runtime_parity_check` で `targets=scala,cs` の parity pass（cases=1/fail=0）を確認。
