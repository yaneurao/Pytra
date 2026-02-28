# Lua Native Backend 契約仕様

<a href="../../en/spec/spec-lua-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`P0-LUA-BACKEND-01` で導入する `EAST3 -> Lua native emitter` 経路の契約を定義する。  
対象は「入力 EAST3 の責務」「未対応時 fail-closed」「runtime 境界」「非対象」である。

## 1. 目的

- Lua backend を sidecar 依存なしの native 直生成として実装する際の責務境界を固定する。
- 初期実装段階でも、対応範囲と未対応時の失敗条件を明文化する。
- 暗黙フォールバック（別言語 backend への退避）で不整合を隠す運用を防ぐ。

## 2. 入力 EAST3 ノード責務

Lua native emitter は以下を満たす EAST3 ドキュメントのみを受理する。

- ルートは `dict` かつ `kind == "Module"`。
- `east_stage == 3`（`--east-stage 2` は受理しない）。
- `body` は EAST3 statement ノード列。

段階責務:

- S1（骨格）: `Module` / `FunctionDef` / `If` / `ForCore` の最小経路。
- S2（本文）: 代入、算術、比較、ループ、呼び出し、組み込み最小セット。
- S3（運用）: class/instance/isinstance/import と `math`・画像 runtime を段階追加。

## 3. fail-closed 契約

未対応入力を受けた場合、互換経路へ逃がさず即時失敗する。

- 未対応 `kind` / shape を検出した時点で `RuntimeError` を送出する。
- エラーメッセージは少なくとも `lang=lua` と failure kind（node/shape）を含む。
- CLI は非 0 で終了し、不完全な `.lua` を成功扱いしない。
- `py2js` / sidecar / EAST2 互換へ暗黙フォールバックしない。

## 4. runtime 境界

Lua 生成コードの runtime 境界は、原則として次に限定する。

- `src/runtime/lua/pytra/` 配下の Lua runtime API（導入後）
- Lua 標準ライブラリ（`math` / `string` / `table` など）

禁止事項:

- Node.js sidecar bridge 依存
- JS runtime shim 前提（`pytra/runtime.js`）
- 生成コードへの巨大 inline helper 埋め込みを既定経路にすること

## 5. 非対象（初期段階）

- 高度最適化（Lua VM 専用チューニング、JIT前提最適化）
- Python 文法・標準ライブラリの完全互換
- PHP backend の同時実装（順序は `Ruby -> Lua -> PHP`）

## 6. 検証観点（初期）

- `py2lua.py` が EAST3 から `.lua` を生成できる。
- 最小 fixture（`add` / `if_else` / `for_range`）で変換失敗しない。
- `tools/check_py2lua_transpile.py` と `test/unit/test_py2lua_smoke.py` で回帰を固定する。
