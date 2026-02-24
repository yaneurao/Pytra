# TASK GROUP: TG-P1-MULTILANG-QUALITY

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo.md` の `ID: P1-MQ-01` 〜 `P1-MQ-07`

背景:
- `sample/cpp/` と比べて、`sample/rs` および他言語（`cs/js/ts/go/java/swift/kotlin`）の生成コードは可読性の劣化が目立つ。
- 不要な `mut`、過剰な括弧・cast・clone、未使用 import などがレビュー/保守コストを押し上げている。
- C++ 以外では selfhost / 多段 selfhost の成立可否が未整理で、実行可能性の判断材料が不足している。
- `sample/py` を毎回 Python 実行して比較すると検証時間が増えるため、ゴールデン出力の保存と再利用導線が必要。

目的:
- 非 C++ 言語の生成コード品質を、`sample/cpp/` と同等の可読性水準まで段階的に引き上げる。

対象:
- `sample/{rs,cs,js,ts,go,java,swift,kotlin}` の出力品質改善
- 各言語の emitter/hooks/profile における冗長出力パターンの削減
- 品質回帰を防ぐ検査項目の追加
- 非 C++ 言語での selfhost 可否（自己変換生成物での再変換）検証
- 非 C++ 言語での多段 selfhost（生成物で再自己変換）検証

非対象:
- 生成コードの意味変更
- runtime 機能追加そのもの
- C++ 出力の追加最適化

受け入れ基準:
- 非 C++ 言語の `sample/` 生成物で、主要冗長パターン（過剰 `mut` / 括弧 / cast / clone / 未使用 import）が段階的に削減される。
- 可読性改善後も既存 transpile/smoke の通過を維持する。
- 品質指標と測定手順が文書化され、回帰時に再測定可能である。
- 非 C++ 各言語について、selfhost 可否と多段 selfhost 可否（1段目/2段目）が同一フォーマットで記録される。
- 失敗言語は、再現手順と失敗カテゴリ（変換失敗 / 実行失敗 / コンパイル失敗 / 出力不一致）まで記録される。
- `sample/` 生成物にタイムスタンプ等の非決定情報を埋め込まず、CI 再生成時に差分ゼロを維持する。
- `sample/py` のゴールデン出力置き場と更新手順（通常比較 / 明示更新）を文書化し、通常検証時に毎回 Python 実行しなくてよい状態にする。

確認コマンド:
- `python3 tools/measure_multilang_quality.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`

`P1-MQ-01` 計測結果:

- ベースラインレポート: `docs-ja/plans/p1-multilang-output-quality-baseline.md`
- 計測対象: `sample/{cpp,rs,cs,js,ts,go,java,swift,kotlin}`
- 主要観測値（`sample/cpp` 比 / kLoC）:
  - `mut`: `rs +334.59`
  - `paren`: `rs +982.59`, `js +824.04`, `ts +818.78`, `cs +309.99`
  - `cast`: `rs +198.12`, `cs +79.87`, `go +73.43`, `java +36.45`
  - `unused_import_est`: `cs +21.14`, `js +6.06`, `ts +6.03`
- 上記は簡易ヒューリスティック計測であり、`unused_import_est` と `cast` は厳密構文解析ではない。

`P1-MQ-02-S1` 実装結果（Rust `mut` 縮退）:

- 対象: `src/hooks/rs/emitter/rs_emitter.py`, `src/profiles/rs/syntax.json`
- 変更点:
  1. 関数本文を事前走査し、束縛名ごとの書き込み回数と破壊的メソッド呼び出し receiver を収集する。
  2. 引数 `mut` は `arg_usage` に加えて、上記の実書き込み/破壊的呼び出しがある場合のみ付与する。
  3. `let mut` 宣言は一律付与をやめ、`write_count` と mutating call 情報に基づいて `let` / `let mut` を切り替える。
  4. `rs` profile の宣言テンプレート（`annassign_decl_*`, `assign_decl_init`）を `{mut_kw}` 対応に変更し、可変性を emitter 側で制御する。
- 生成物反映:
  - `python3 tools/regenerate_samples.py --langs rs --force` で `sample/rs` を再生成。
  - `sample/rs/01_mandelbrot.rs` では `x2/y2/t/r/g/b/width/height/max_iter/...` の不要 `mut` が除去されることを確認。
- 指標変化（`sample/cpp` 比較の生カウント）:
  - `rs mut`: `711 -> 609`
  - `rs paren`: `2347 -> 821`
  - `rs cast`: `421 -> 180`
  - `rs clone`: `18 -> 1`

`P1-MQ-02-S2` 実装結果（JS/TS 括弧・import 縮退）:

- 対象: `src/hooks/js/emitter/js_emitter.py`
- 変更点:
  1. `BinOp` / `BoolOp` / `Compare` / `UnaryOp` の式描画で、意味保持に必要な最小限の括弧のみを残すようにした。
  2. `import_bindings` と AST 走査結果から未使用識別子を除外し、`import` 文の過剰出力を削減した。
  3. `py_runtime` の展開シンボルを「実際に必要な型ID関連シンボルのみ」へ縮退し、不要な destructuring を削減した。
- 生成物反映:
  - `python3 tools/regenerate_samples.py --langs js,ts --force` で `sample/js` / `sample/ts` を再生成。
- 指標変化（`sample/cpp` 比較の生カウント）:
  - `js paren`: `2029 -> 148`
  - `ts paren`: `2029 -> 148`
  - `js imports`: `75 -> 49`
  - `ts imports`: `75 -> 49`
  - `js unused_import_est`: `13 -> 0`
  - `ts unused_import_est`: `13 -> 0`

`P1-MQ-02-S3-S1` 実装結果（C# cast/import/paren 縮退）:

- 対象: `src/hooks/cs/emitter/cs_emitter.py`
- 変更点:
  1. `import_bindings` と AST 走査結果から未使用識別子を除外し、`using` の過剰出力を抑制した。
  2. `List` / `Dictionary` / `HashSet` / `IEnumerable` などを完全修飾名へ寄せ、既定 `using` 依存を削減した。
  3. `BinOp` / `BoolOp` / `Compare` / `UnaryOp` の式描画で最小括弧化を行い、`((`/`))` を削減した。
  4. `FloorDiv` と `Subscript` の `(long|double|int)` 直キャストを `System.Convert` 経由へ置換した。
- 生成物反映:
  - `python3 tools/regenerate_samples.py --langs cs --force` で `sample/cs` を再生成。
- 指標変化（`sample/cpp` 比較の生カウント）:
  - `cs paren`: `1103 -> 215`
  - `cs cast`: `204 -> 0`
  - `cs imports`: `55 -> 7`
  - `cs unused_import_est`: `54 -> 0`

`P1-MQ-02-S3-S2` 実装結果（Go/Java preview 冗長縮退）:

- 対象: `src/hooks/go/emitter/go_emitter.py`, `src/hooks/java/emitter/java_emitter.py`
- 変更点:
  1. Go/Java preview で C# 全文コメント埋め込みをやめ、シグネチャ中心の軽量要約出力へ切り替えた。
  2. `using` 行や本体ステートメントは埋め込まず、`public` シグネチャとコメント行のみを抽出するフィルタを導入した。
  3. Go/Java transpiler minor version を `0.3.0` へ更新した（`transpiler_versions.json`）。
- 生成物反映:
  - `python3 tools/regenerate_samples.py --langs go,java --force` で `sample/go` / `sample/java` を再生成。
- 指標変化（`sample/cpp` 比較の生カウント）:
  - `go paren`: `1572 -> 0`
  - `go cast`: `844 -> 0`
  - `go imports`: `120 -> 0`
  - `java paren`: `1727 -> 0`
  - `java cast`: `413 -> 0`
  - `java imports`: `132 -> 0`

`P1-MQ-02-S3-S3` 実装結果（Swift/Kotlin preview 冗長縮退）:

- 対象: `src/hooks/swift/emitter/swift_emitter.py`, `src/hooks/kotlin/emitter/kotlin_emitter.py`
- 変更点:
  1. Swift/Kotlin preview で C# 全文埋め込みをやめ、シグネチャ要約コメントへ切り替えた。
  2. Swift 既定 `import Foundation` を撤去し、未使用 import を解消した。
  3. Swift/Kotlin transpiler minor version を `0.3.0` へ更新した（`transpiler_versions.json`）。
- 生成物反映:
  - `python3 tools/regenerate_samples.py --langs swift,kotlin --force` で `sample/swift` / `sample/kotlin` を再生成。
- 指標変化（`sample/cpp` 比較の生カウント）:
  - `swift paren`: `296 -> 0`
  - `swift imports`: `18 -> 0`
  - `swift unused_import_est`: `6 -> 0`
  - `kotlin paren`: `296 -> 0`
  - `kotlin cast`: `12 -> 0`
  - `kotlin imports`: `60 -> 0`

決定ログ:
- 2026-02-22: 初版作成（`sample/cpp` 水準を目標に、非 C++ 言語の出力品質改善を TODO 化）。
- 2026-02-22: `P1-MQ-08` として `tools/verify_sample_outputs.py` をゴールデン比較運用へ切り替えた。既定は `sample/golden/manifest.json` 参照 + C++ 実行結果比較とし、Python 実行は `--refresh-golden`（更新のみは `--refresh-golden-only`）指定時のみ実行する方針にした。
- 2026-02-24: ID: P1-MQ-01 として `tools/measure_multilang_quality.py` を追加し、`docs-ja/plans/p1-multilang-output-quality-baseline.md` に `sample/cpp` 比の品質差分（`mut`/`paren`/`cast`/`clone`/`unused_import_est`）を定量化した。
- 2026-02-24: ID: P1-MQ-02-S1 として Rust emitter の `mut` 付与を事前解析ベースへ切り替え、`sample/rs` 再生成と品質再計測で `mut`/`paren`/`cast`/`clone` の減少を確認した。
- 2026-02-24: ID: P1-MQ-02-S2 として JS emitter の括弧最小化・import/runtime symbol 縮退を実装し、`sample/js` / `sample/ts` の `paren` と `unused_import_est` の大幅減少を確認した。
- 2026-02-24: ID: P1-MQ-02-S3-S1 として C# emitter の cast/import/括弧縮退を実施し、`sample/cs` の `paren`/`cast`/`imports`/`unused_import_est` を大幅削減した。
- 2026-02-24: ID: P1-MQ-02-S3-S2 として Go/Java preview 出力をシグネチャ要約へ縮退し、`sample/go` / `sample/java` の `paren`/`cast`/`imports` を削減した。
- 2026-02-24: ID: P1-MQ-02-S3-S3 として Swift/Kotlin preview 出力をシグネチャ要約へ縮退し、`sample/swift` / `sample/kotlin` の `paren`/`cast`/`imports`/`unused_import_est` を削減した。
