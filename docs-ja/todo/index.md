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

### `src/py2cpp.py`

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
3. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
4. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- 詳細ログは `docs-ja/plans/p3-pythonic-restoration.md` の `決定ログ` を参照。

### 作業ルール

1. [ ] [ID: P3-RULE-01] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] [ID: P3-RULE-02] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] [ID: P3-RULE-03] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] [ID: P3-RULE-04] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## P3: サンプル実行時間の再計測とREADME更新（低優先）

文脈: `docs-ja/plans/p3-sample-benchmark-refresh.md`（`TG-P3-SAMPLE-BENCHMARK`）

1. [ ] [ID: P3-SB-01] サンプルコード変更（実行時間変化）、サンプル番号再編（04/15/17/18）、サンプル数増加（01〜18）を反映するため、全ターゲット言語（Python/C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）で実行時間を再計測し、トップページの `readme.md` / `readme-ja.md` の比較表を同一データで更新する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。
