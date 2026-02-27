# Ruby Native Backend 契約仕様

<a href="../../docs/spec/spec-ruby-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`P2-RUBY-BACKEND-01` で導入する `EAST3 -> Ruby native emitter` 経路の契約を定義する。  
対象は「入力 EAST3 の責務」「未対応時 fail-closed」「runtime 境界」「非対象」である。

## 1. 目的

- Ruby backend を sidecar 互換に頼らない native 直生成として実装する際の境界を固定する。
- 実装初期段階でも、対応範囲と未対応時の失敗条件を明文化する。
- 既存 backend と同様に、暗黙フォールバックで不整合を隠す運用を防ぐ。

## 2. 入力 EAST3 ノード責務

Ruby native emitter は以下を満たす EAST3 ドキュメントのみを受理する。

- ルートは `dict` かつ `kind == "Module"`。
- `east_stage == 3`（`--east-stage 2` は受理しない）。
- `body` は EAST3 statement ノード列。

段階責務:

- S1（骨格）: `Module` / `FunctionDef` / `ForCore` / `If` の最小経路。
- S2（本文）: 代入、算術、比較、ループ、呼び出し、組み込み最小セット。
- S3（運用）: class/instance/isinstance/import と `math`・画像 runtime を段階追加。

## 3. fail-closed 契約

未対応入力を受けた場合、互換経路へ逃がさず即時失敗する。

- 未対応 `kind` / 契約違反を検出した時点で `RuntimeError` を送出する。
- エラーメッセージは少なくとも `lang=ruby` と failure kind（node/shape）を含む。
- CLI は非 0 で終了し、不完全な `.rb` を成功扱いしない。

## 4. runtime 境界

Ruby 生成コードの runtime 境界は、原則として次に限定する。

- 生成物内の最小 helper（`__pytra_*`）
- Ruby 標準ライブラリ（`Math` など）

禁止事項:

- Node.js sidecar bridge 依存
- JS runtime shim 前提 (`pytra/runtime.js`)
- 非同期に別 backend へフォールバックする互換導線

## 5. 非対象（初期段階）

- 高度最適化（最適化層導入、Ruby VM 依存高速化）
- すべての Python 文法・標準ライブラリ完全互換
- PHP/Lua backend の同時実装（順序は `Ruby -> Lua -> PHP`）

## 6. 検証観点（初期）

- `py2rb.py` が EAST3 から `.rb` を生成できる。
- 最小 fixture（`add` / `if_else` / `for_range`）で変換失敗しない。
- `test/unit/test_py2rb_smoke.py` で CLI と emitter 骨格の回帰を固定する。
