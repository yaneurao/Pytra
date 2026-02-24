# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-24

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## P0: EAST123 最終移行（最優先・継続）

文脈: `docs-ja/plans/plan-east123-migration.md`（`TG-P0-EAST123-MIGRATION`）

1. [ ] [ID: P0-EASTMIG-06] `EAST3` を全変換器の標準主経路として確定し、`EAST2` は明示互換モードに限定する（`P0-EASTMIG-06-S10` 完了でクローズ）。
2. [ ] [ID: P0-EASTMIG-06-S10] `check_selfhost_cpp_diff.py --mode allow-not-implemented` で検出された `sample/py/01_mandelbrot.py` と `sample/py/17_monte_carlo_pi.py` の差分原因を切り分け、`P0-EASTMIG-06` の最終クローズ条件を確定する。

## P1: 多言語出力品質（preview 脱却の再オープン）

文脈: `docs-ja/plans/p1-multilang-output-quality.md`（`TG-P1-MULTILANG-QUALITY`）

1. [ ] [ID: P1-MQ-10] `sample/go`, `sample/kotlin`, `sample/swift` の preview 要約出力（「C# ベース中間出力のシグネチャ要約」）を廃止し、通常のコード生成へ移行する（`P1-MQ-10-S1` から `P1-MQ-10-S4` 完了でクローズ）。
2. [ ] [ID: P1-MQ-10-S1] GoEmitter の CodeEmitter ベース実装を拡張し、`sample/go` が要約コメントではなく AST 本文を出力するようにする。
3. [ ] [ID: P1-MQ-10-S2] KotlinEmitter の CodeEmitter ベース実装を拡張し、`sample/kotlin` が要約コメントではなく AST 本文を出力するようにする。
4. [ ] [ID: P1-MQ-10-S3] SwiftEmitter の CodeEmitter ベース実装を拡張し、`sample/swift` が要約コメントではなく AST 本文を出力するようにする。
5. [ ] [ID: P1-MQ-10-S4] `tools/check_py2{go,kotlin,swift}_transpile.py` と `tools/check_multilang_quality_regression.py` に「preview 要約出力禁止」検査を追加し、`sample/go`, `sample/kotlin`, `sample/swift` の先頭 `TODO: 専用 *Emitter 実装へ段階移行` 文言が再流入しないようにする。

## P1: 多言語ランタイム配置統一（再オープン）

文脈: `docs-ja/plans/p1-runtime-layout-unification.md`（`TG-P1-RUNTIME-LAYOUT`）

1. [ ] [ID: P1-RUNTIME-06] `src/{cs,go,java,kotlin,swift}_module/` の runtime 実体を `src/runtime/<lang>/pytra/` へ移行し、`src/*_module/` を shim-only または削除状態へ収束させる（`P1-RUNTIME-06-S1` から `P1-RUNTIME-06-S6` 完了でクローズ）。
2. [ ] [ID: P1-RUNTIME-06-S1] C# runtime 実体（`src/cs_module/*`）を `src/runtime/cs/pytra/` へ移し、参照/namespace/テストを新配置へ合わせる。
3. [ ] [ID: P1-RUNTIME-06-S2] Go runtime 実体（`src/go_module/py_runtime.go`）を `src/runtime/go/pytra/` へ移し、参照と smoke 検証を新配置へ合わせる。
4. [ ] [ID: P1-RUNTIME-06-S3] Java runtime 実体（`src/java_module/PyRuntime.java`）を `src/runtime/java/pytra/` へ移し、参照と smoke 検証を新配置へ合わせる。
5. [ ] [ID: P1-RUNTIME-06-S4] Kotlin runtime 実体（`src/kotlin_module/py_runtime.kt`）を `src/runtime/kotlin/pytra/` へ移し、参照と smoke 検証を新配置へ合わせる。
6. [ ] [ID: P1-RUNTIME-06-S5] Swift runtime 実体（`src/swift_module/py_runtime.swift`）を `src/runtime/swift/pytra/` へ移し、参照と smoke 検証を新配置へ合わせる。
7. [ ] [ID: P1-RUNTIME-06-S6] `tools/check_runtime_legacy_shims.py` と関連 docs を更新し、`src/{cs,go,java,kotlin,swift}_module/` に実体ファイルが再流入しない CI ガードを追加する。

## P1: 多言語出力品質（高優先）

文脈: `docs-ja/plans/p1-multilang-output-quality.md`（`TG-P1-MULTILANG-QUALITY`）

1. [ ] [ID: P1-MQ-09] Rust emitter の `BinOp` で発生している過剰括弧（例: `y = (((2.0 * x) * y) + cy);`）を最小化し、`sample/rs` を再生成して可読性を `sample/cpp` 水準へ戻す。実施後は `tools/measure_multilang_quality.py` の `rs paren` 指標を再計測し、`tools/check_multilang_quality_regression.py` の基線を更新して再発を防止する。

## P3: Pythonic 記法戻し（低優先）

文脈: `docs-ja/plans/p3-pythonic-restoration.md`（`TG-P3-PYTHONIC`）

### `src/pytra/compiler/east_parts/`（先行）

1. [ ] [ID: P3-EAST-PY-01] `src/pytra/compiler/east_parts/{code_emitter.py,core.py}` で selfhost 安定化のために残した非 Pythonic 記法（`while i < len(...)`、手動 index 走査、冗長な空判定）を棚卸しし、`Pythonic へ戻せる/戻せない` の判定表を作る。
2. [ ] [ID: P3-EAST-PY-02] `P3-EAST-PY-01` で「戻せる」と判定した `code_emitter.py` の非 Pythonic 記法を、1パッチ 1〜3 関数の粒度で `for` / `enumerate` / 直接反復へ戻す。
3. [ ] [ID: P3-EAST-PY-03] `P3-EAST-PY-01` で「戻せる」と判定した `core.py` の非 Pythonic 記法を、selfhost 回帰が出ない範囲で段階的に戻す。
4. [ ] [ID: P3-EAST-PY-04] `P3-EAST-PY-02` と `P3-EAST-PY-03` の結果を `docs-ja/plans/p3-pythonic-restoration.md` に反映し、残る非 Pythonic 記法の維持理由（selfhost 制約）を明文化する。

### `src/py2cpp.py`

`P3-EAST-PY-*` を先行し、`east_parts` 側の整理完了後に着手する。

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
3. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
4. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- 詳細ログは `docs-ja/plans/p3-pythonic-restoration.md` の `決定ログ` を参照。
- 作業ルールは `docs-ja/plans/p3-pythonic-restoration.md` の「作業ルール」を参照。

## P3: サンプル実行時間の再計測とREADME更新（低優先）

文脈: `docs-ja/plans/p3-sample-benchmark-refresh.md`（`TG-P3-SAMPLE-BENCHMARK`）

1. [ ] [ID: P3-SB-01] サンプルコード変更（実行時間変化）、サンプル番号再編（04/15/17/18）、サンプル数増加（01〜18）を反映するため、全ターゲット言語（Python/C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）で実行時間を再計測し、トップページの `readme.md` / `readme-ja.md` の比較表を同一データで更新する。

## P3: `pytra` ランチャーと build 導線実装（低優先）

文脈: `docs-ja/plans/p3-pytra-launcher-build.md`（`TG-P3-LAUNCHER-BUILD`）

1. [ ] [ID: P3-LB-01] `spec-make` の未実装項目（`./pytra` ランチャー / `src/pytra/cli.py` / `tools/gen_makefile_from_manifest.py` / `--target cpp --build`）を実装し、C++ の「変換 -> Makefile 生成 -> build」導線を 1 コマンドで実行できるようにする（`P3-LB-01-S1` から `P3-LB-01-S4` 完了でクローズ）。
2. [ ] [ID: P3-LB-01-S1] `tools/gen_makefile_from_manifest.py` を追加し、`manifest.json` から `Makefile`（`all/run/clean`）を生成できるようにする。
3. [ ] [ID: P3-LB-01-S2] `src/pytra/cli.py` を追加し、`./pytra INPUT.py --target cpp --build` で `py2cpp --multi-file` -> Makefile 生成 -> `make` 実行までを連結できるようにする。
4. [ ] [ID: P3-LB-01-S3] リポジトリ直下に `./pytra` ランチャーを追加し、`PYTHONPATH=src` の手動設定なしで `python3 -m pytra.cli` を起動できるようにする。
5. [ ] [ID: P3-LB-01-S4] `tools` / CLI の unit test とドキュメント（`spec-make.md` / `spec-dev.md` / `spec-tools.md`）を同期し、未実装表記を解消する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。
