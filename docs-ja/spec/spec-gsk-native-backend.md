# Go/Swift/Kotlin Native Backend 契約仕様

<a href="../../docs/spec/spec-gsk-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`P3-GSK-NATIVE-01` で導入する `EAST3 -> Go/Swift/Kotlin native emitter` 経路の共通契約を定義する。  
対象は「入力 EAST3 の責務」「未対応時 fail-closed」「runtime 境界」「sidecar 既定撤去時の運用要件」である。

## 1. 目的

- Go / Swift / Kotlin backend の既定経路を sidecar bridge から native 生成へ移行する際の責務境界を固定する。
- 言語ごとの差分を許容しつつ、未対応時の失敗動作と runtime 境界を共通化する。
- `sample/go` / `sample/swift` / `sample/kotlin` が preview ラッパーへ戻る回帰を防ぐ。

## 2. sidecar 出力との差分

現行（preview / sidecar）:

- `py2go.py` / `py2swift.py` / `py2kotlin.py` は sidecar JavaScript を生成し、各言語側は Node bridge ラッパーを出力する。
- 生成コードは実ロジック本体を持たず、`node <sidecar.js>` 実行の薄いラッパーになりやすい。
- runtime 依存は `<lang> runtime + Node.js + JS runtime shim` である。

移行後（native）:

- 既定経路は native emitter のみを通し、`.js` sidecar を生成しない。
- 生成コードは EAST3 本文ロジック（式/文/制御/クラス）を各言語コードとして直接保持する。
- sidecar は明示 opt-in の互換モードに隔離し、既定では使用しない。

## 3. 入力 EAST3 ノード責務

native emitter は次の入力契約を満たす EAST3 ドキュメントのみを受理する。

- ルートは `dict` かつ `kind == "Module"`。
- `east_stage == 3` であること（`--east-stage 2` は受理しない）。
- `body` は EAST3 statement ノード列であること。

共通の段階責務:

- S1（骨格）: `Module` / `FunctionDef` / `ClassDef` の枠組みを処理する。
- S2（本文）: `Return` / `Expr` / `AnnAssign` / `Assign` / `If` / `ForCore` / `While` と主要式（`Name` / `Constant` / `Call` / `BinOp` / `Compare`）を処理する。
- S3（運用）: `sample/py` 主要ケースで必要な `math` / 画像 runtime 呼び出しを最小互換として処理する。

## 4. fail-closed 契約

native 経路では「未対応入力を暗黙に sidecar へフォールバック」してはならない。

- 未対応ノード `kind` を検出した場合は即時失敗（`RuntimeError` 相当）する。
- エラー文面には少なくとも `lang`, `node kind`, `location`（可能な範囲）を含める。
- CLI は非 0 終了し、不完全な生成物を成功扱いで出力しない。
- 互換 sidecar 経路を残す場合も、明示指定時のみ利用可能にする。

## 5. runtime 境界

native 生成物は次の runtime 境界のみを利用する。

- Go: `src/runtime/go/pytra/py_runtime.go` + Go 標準ライブラリ。
- Swift: `src/runtime/swift/pytra/py_runtime.swift` + Swift 標準ライブラリ。
- Kotlin: `src/runtime/kotlin/pytra/py_runtime.kt` + Kotlin/JVM 標準ライブラリ。

禁止事項（既定経路）:

- `ProcessBuilder` / `exec` 等で Node.js を起動する bridge 実装。
- `.js` sidecar 生成と `sample/<lang>/*.js` 依存。
- 生成物内での JS bridge 前提 import。

## 6. 移行時の検証観点

- `tools/check_py2go_transpile.py` / `tools/check_py2swift_transpile.py` / `tools/check_py2kotlin_transpile.py` が native 既定で通る。
- `tools/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --all-samples --ignore-unstable-stdout` で Python 基準との出力一致を監視する。
- `sample/go` / `sample/swift` / `sample/kotlin` 再生成時に sidecar `.js` が残らないことを確認する。

## 7. sidecar 互換モード隔離方針（S1-02）

- 既定挙動は常に native とし、次の明示フラグ指定時のみ sidecar を許可する。
  - Go: `--go-backend sidecar`
  - Swift: `--swift-backend sidecar`
  - Kotlin: `--kotlin-backend sidecar`
- native 指定（または省略）時は `.js` sidecar と JS runtime shim を生成しない。
- sidecar 指定時は互換モードとして `.js` 生成を許可するが、CI の既定回帰対象からは外す。
- 既定経路で unsupported を検出した場合、sidecar へ自動フォールバックせず fail-closed で停止する。
