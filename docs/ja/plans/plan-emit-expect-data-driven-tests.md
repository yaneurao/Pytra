# 計画: emitter テストのデータ駆動化

## 背景

`tools/unittest/toolchain2/test_common_renderer.py` に emitter 出力のテストケースが Python unittest メソッドとして増え続けている。各テストの本質は「EAST3 ノード(入力) → emit 文字列(期待出力)」のペアであり、Python コードで記述する必要がない。

言語ごとに smoke テストスクリプトを作ることも禁止されている（spec-emitter-guide §13）が、同じ問題が `test_common_renderer.py` 内のメソッド増殖という形で起きている。

## 提案

### 1. テストケースを JSON ファイルで記述する

`test/fixture/emit-expect/<lang>/` に JSON ファイルを配置する:

```json
{
  "description": "nested binop respects precedence",
  "target": "cpp",
  "input": {
    "kind": "BinOp",
    "left": {
      "kind": "BinOp",
      "left": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
      "op": "Add",
      "right": {"kind": "Constant", "value": 2, "resolved_type": "int64"},
      "resolved_type": "int64"
    },
    "op": "Mult",
    "right": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
    "resolved_type": "int64"
  },
  "expected": "(int64(1) + int64(2)) * int64(3)"
}
```

### 2. テストランナーは1つだけ

`pytest.mark.parametrize` でディレクトリ内の全 JSON を走査する汎用テストランナーを1本だけ用意する。ケース追加は JSON ファイルを置くだけで、Python コードの変更は不要。

### 3. 既存テストの移行

`test_common_renderer.py` 内の emitter 出力テスト（`test_cpp_emitter_*` 系）を段階的に JSON ケースへ移行する。emitter の初期化やコンテキスト構築に Python コードが必要なテストは残してよい。

## 利点

- ケース追加が JSON ファイル追加のみで済む（Python コード変更不要）
- テストケースの一覧性が高い（ファイル名で内容がわかる）
- 言語横断で同じ仕組みを使える（`emit-expect/cpp/`, `emit-expect/go/`, ...）
- テストスクリプトの肥大化を防げる

## 注意点

- 式レベルのテスト（`emit_cpp_expr`）と文レベルのテスト（`emit_cpp_stmt`）を JSON の `"level": "expr" | "stmt"` で区別する必要がある
- emitter コンテキスト（EmitContext）のカスタマイズが必要なケースは JSON では表現しにくい — これらは Python テストに残す

## ステータス

保留中。既存テストが他 agent により変更中のため、安定してから着手する。
