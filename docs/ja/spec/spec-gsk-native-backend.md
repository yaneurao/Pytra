<a href="../../en/spec/spec-gsk-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Go/Swift/Kotlin Native Backend 契約仕様

この文書は、`P3-GSK-NATIVE-01` で導入した `EAST3 -> Go/Swift/Kotlin native emitter` 経路の共通契約を定義する。  
対象は「入力 EAST3 の責務」「未対応時 fail-closed」「runtime 境界」「sidecar 撤去後の運用要件」である。

## 1. 目的

- Go / Swift / Kotlin backend の既定経路を sidecar bridge から native 生成へ移行する際の責務境界を固定する。
- 言語ごとの差分を許容しつつ、未対応時の失敗動作と runtime 境界を共通化する。
- `sample/go` / `sample/swift` / `sample/kotlin` が preview ラッパーへ戻る回帰を防ぐ。

## 2. sidecar 旧経路との差分

旧経路（preview / sidecar, 撤去済み）:

- `py2go.py` / `py2swift.py` / `py2kotlin.py` は sidecar JavaScript を生成し、各言語側は Node bridge ラッパーを出力する。
- 生成コードは実ロジック本体を持たず、`node <sidecar.js>` 実行の薄いラッパーになりやすい。
- runtime 依存は `<lang> runtime + Node.js + JS runtime shim` である。

移行後（native）:

- 既定経路は native emitter のみを通し、`.js` sidecar を生成しない。
- 生成コードは EAST3 本文ロジック（式/文/制御/クラス）を各言語コードとして直接保持する。
- sidecar 互換モードは廃止し、native 単一路線で運用する。

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
- 未対応入力を sidecar へ逃がす回避経路は持たない。

## 5. runtime 境界

native 生成物は次の runtime 境界のみを利用する。

- Go: `src/runtime/go/{generated,native}/` + Go 標準ライブラリ。
- Swift: `src/runtime/swift/{generated,native}/` + Swift 標準ライブラリ。
- Kotlin: `src/runtime/kotlin/{generated,native}/` + Kotlin/JVM 標準ライブラリ。

禁止事項（既定経路）:

- `ProcessBuilder` / `exec` 等で Node.js を起動する bridge 実装。
- `.js` sidecar 生成と `sample/<lang>/*.js` 依存。
- 生成物内での JS bridge 前提 import。

## 6. 移行時の検証観点

- `tools/check_py2go_transpile.py` / `tools/check_py2swift_transpile.py` / `tools/check_py2kotlin_transpile.py` が native 既定で通る。
- `tools/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --all-samples --ignore-unstable-stdout` で Python 基準との出力一致を監視する。
- `sample/go` / `sample/swift` / `sample/kotlin` 再生成時に sidecar `.js` が残らないことを確認する。

## 7. sidecar 撤去方針（S1-02）

- `py2go.py` / `py2swift.py` / `py2kotlin.py` から `--*-backend sidecar` を削除し、backend 切替点を撤去する。
- 生成経路は native のみとし、`.js` sidecar / JS runtime shim を一切生成しない。
- CI の既定回帰・sample 再生成・parity 検証は native 経路のみを監視対象とする。
- 既定経路で unsupported を検出した場合は fail-closed で停止する（sidecar への自動/手動退避は不可）。

## 8. コンテナ参照管理境界（v1）

- 共通語彙:
  - `container_ref_boundary`: `Any/object/unknown/union(any含む)` へ流入する経路。
  - `typed_non_escape_value_path`: 型既知で局所 non-escape な経路。
- 運用規則:
  - `container_ref_boundary` は参照として扱い、不要な暗黙コピーを避ける。
  - `typed_non_escape_value_path` は shallow copy 材料化を許可する（alias 分離を優先）。
  - 判定不能時は fail-closed で `container_ref_boundary` へ倒す。
- rollback:
  - 生成差分で問題が出た箇所は、入力側の型注釈を `Any/object` に寄せて ref-boundary を強制する。
  - 検証は `check_py2{go,swift,kotlin}_transpile.py` と `runtime_parity_check.py` を併用する。
