# P1: sample 多言語出力の型既知 fastpath 強化（品質改善）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-SAMPLE-OUTPUT-QUALITY-01`

背景:
- `sample/` の生成コードには、意味は一致しても型既知経路で `Any/Object` へ退化する箇所や、helper/cast 呼び出し過多の箇所が多く残る。
- とくに `go/java/kotlin/swift/scala` で `Any/Object` 依存が厚く、`rs/js/ts` でもループ/一時変数の冗長が目立つ。

目的:
- 型既知な式・コンテナ・ループで native 表現を優先し、生成コードの可読性と実行効率を同時に改善する。

対象:
- `src/hooks/{go,java,kotlin,swift,scala,rs,js,ts}/emitter/*.py`
- `src/py2{go,java,kotlin,swift,scala,rs,js,ts}.py`
- `sample/{go,java,kotlin,swift,scala,rs,js,ts}/*.*`
- 関連 unit/golden テスト

非対象:
- 仕様追加（新構文対応、新 builtin 対応）
- runtime API の大規模刷新

受け入れ基準:
- `sample/01` と `sample/18` で、型既知経路の `Any/Object` 退化・不要 helper 呼び出しが削減される。
- `for __for_i ...; i = __for_i;` や `const __start_N = 0` などの冗長 loop 形が縮退する。
- 言語別 smoke/transpile チェックと parity（最低 `01/18`）が通過する。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts*' -v`
- `python3 tools/regenerate_samples.py --langs go,java,kotlin,swift,scala,rs,js,ts --stems 01_mandelbrot,18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,java,kotlin,swift,scala,rs,js,ts --ignore-unstable-stdout 01_mandelbrot 18_mini_language_interpreter`

分解:
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-01] `go/java` の `Any/Object` 退化 hotspot（`sample/18`）を棚卸しし、typed fastpath の適用境界を固定する。
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-02] `kotlin/swift/scala` の helper/cast 連鎖（`__pytra_int/float`, `asInstanceOf`）を棚卸しし、削減優先順を確定する。
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-03] `rs/js/ts` のループ冗長パターン（`__for_i` 再代入、`__start_N`）の縮退規則を仕様化する。
- [ ] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] `go/java` emitter に typed container/typed access fastpath を実装する。
- [ ] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] `kotlin/swift/scala` emitter に cast/helper 抑制 fastpath を実装する。
- [ ] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] `rs/js/ts` emitter に canonical loop 出力を実装し、冗長一時変数を削減する。
- [ ] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] 言語別回帰テストを追加し、退化再発を検知可能にする。
- [ ] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-02] 対象 sample を再生成し、smoke/transpile/parity で非退行を確認する。

決定ログ:
- 2026-03-02: sample 多言語品質調査の結果を受け、型既知 fastpath を中心とする横断改善を P1 へ起票した。
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-01] `sample/go/18` と `sample/java/18` を棚卸し。`[]any` / `ArrayList<Object>`・`map[any]any` / `HashMap<Object,Object>`・`enumerate` 展開で `line_index/source` が untyped 化していることを確認。`S2-01` の適用境界を「(a) list/tuple/dict の resolved_type が閉じている、(b) loop target plan が Name/Tuple で型注釈がある、(c) `py_*` helper が object 境界を要求しない箇所」に固定。
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-02] `sample/{kotlin,swift,scala}/18` を棚卸し。`__pytra_int(...)` の同型再キャスト連鎖、`asInstanceOf` / `as? ... ??` の防御キャスト、`__pytra_as_list(...typed literal...)` が主要ノイズと判定。削減優先順は 1) 同型 cast/helper 除去、2) typed literal 直出力、3) container access の typed fastpath 化。
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-03] `sample/{rs,js,ts}/18` を棚卸し。`rs` は `for __for_i_N ...; i = __for_i_N`、`js/ts` は `const __start_N = 0; for (let i = __start_N; ...)` が冗長パターン。`S2-03` 規則を「定数開始値は直接埋め込み」「range 直列は target へ直接束縛」「再代入のみの中継変数を emit しない」に固定。

実装境界メモ（S1 集約）:
- `go/java` typed fastpath は `tokenize/parse_program/execute/build_benchmark_source` の container と loop target を優先対象にする。
- `kotlin/swift/scala` cast/helper 削減は `parse_*` / `eval_expr` の `int64` 既知経路を優先し、`object` 境界（辞書/動的 index）では fail-closed を維持する。
- `rs/js/ts` loop 縮退は `StaticRangeForPlan` 由来の単純 range に限定し、`step` 非定数や比較式差し替え経路は対象外とする。
