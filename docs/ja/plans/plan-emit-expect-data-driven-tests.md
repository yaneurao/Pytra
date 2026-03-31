# 計画: unittest のデータ駆動化 (P20-DATA-DRIVEN-TESTS)

## 背景

`tools/unittest/` に 269 個のテストスクリプトがあり、増え続けている。しかし大半のテストの本質は:

- **入力**: Python ソース文字列 or EAST JSON
- **操作**: parse / resolve / lower / emit のどれか
- **期待**: 出力文字列 or JSON の一部一致

これは Python コードで書く必要がなく、JSON データで定義できる。テストスクリプトが増殖するのは「テストケース = Python コード」という前提のせいであり、設計を変えるべき。

言語ごとの smoke テストスクリプトは spec-emitter-guide §13 で禁止されているが、同じ問題が `test_common_renderer.py` のメソッド増殖や `tools/unittest/emit/<lang>/` のスクリプト増殖として起きている。

## 設計

### ディレクトリ構成

```
test/cases/
  east1/                    # parse テスト
    for_range_normalization.json
    range_expr_lowering.json
  east2/                    # resolve テスト
    type_inference_int.json
    isinstance_narrowing.json
  east3/                    # lowering テスト
    closure_def_capture.json
    block_scope_hoist.json
  emit/                     # emitter テスト
    cpp/
      binop_precedence.json
      literal_no_wrap.json
    go/
      container_wrapper.json
    rs/
      trait_dispatch.json
```

### JSON テストケース形式

#### パイプラインテスト（east1/east2/east3）

```json
{
  "description": "isinstance narrowing resolves dict type in if block",
  "pipeline": "source_to_east3",
  "input": "def f(x: object) -> str:\n  if isinstance(x, str):\n    return x\n  return ''",
  "assertions": [
    {"path": "body[0].body[0].body[0].value.resolved_type", "equals": "str"},
    {"path": "body[0].body[0].test.resolved_type", "equals": "bool"}
  ]
}
```

`pipeline` の値:
- `source_to_east1`: parse のみ
- `source_to_east2`: parse + resolve
- `source_to_east3`: parse + resolve + lower
- `east3_to_linked`: link まで

`assertions` の形式:
- `{"path": "json.path.expr", "equals": "value"}` — 完全一致
- `{"path": "json.path.expr", "contains": "substring"}` — 部分一致
- `{"path": "json.path.expr", "not_equals": "value"}` — 不一致
- `{"path": "json.path.expr", "exists": true}` — 存在確認

#### emitter テスト（emit/）

```json
{
  "description": "nested binop respects precedence",
  "target": "cpp",
  "level": "expr",
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

`level` の値:
- `expr`: 式レベル emit（`emit_cpp_expr` 等）
- `stmt`: 文レベル emit
- `module`: ソース文字列 → emit（end-to-end）

`module` レベルの場合:

```json
{
  "description": "for range emits C++ for loop",
  "target": "cpp",
  "level": "module",
  "input": "def f() -> None:\n  for i in range(10):\n    print(i)",
  "expected_contains": ["for (int64 i = 0; i < 10;", "py_print(i)"]
}
```

### テストランナー

テストランナーは **2本** だけ:

1. `tools/unittest/test_pipeline_cases.py` — `test/cases/{east1,east2,east3}/` を走査
2. `tools/unittest/test_emit_cases.py` — `test/cases/emit/<lang>/` を走査

どちらも `pytest.mark.parametrize` で JSON ファイルを動的収集。ケース追加は JSON ファイルを置くだけ。

### Python テストとして残すもの

以下は JSON では表現しにくいため、Python テストとして残す:

- emitter コンテキスト（EmitContext）のカスタマイズが必要なテスト
- 複数ファイル間の import 解決テスト
- selfhost golden 比較テスト
- ファイルシステム操作を伴うテスト（compile + run）

## 移行計画

### Phase 1: emit 層で方式を確立

1. `test/cases/emit/cpp/` に JSON テストケース 5〜10 件を作成
2. `tools/unittest/test_emit_cases.py` を実装
3. `test_common_renderer.py` の対応テストを JSON に移行し、元メソッドを削除
4. 動作確認

### Phase 2: パイプライン層に横展開

1. `test/cases/east3/` に JSON テストケースを作成（isinstance narrowing, closure capture 等）
2. `tools/unittest/test_pipeline_cases.py` を実装
3. `tools/unittest/toolchain2/` の対応テストを段階的に JSON に移行

### Phase 3: 既存スクリプトの縮退

1. JSON に移行済みのテストメソッドを Python スクリプトから削除
2. 空になったスクリプトを削除
3. `tools/unittest/emit/<lang>/` の言語別スクリプトを段階的に JSON に移行

## 利点

- ケース追加が JSON ファイル追加のみ（Python コード変更不要）
- テストケースの一覧性が高い（ファイル名で内容がわかる）
- 言語横断で同じ仕組みを使える
- テストスクリプトの肥大化を防げる
- agent がテストを追加するときに既存スクリプトを読む必要がない

## ステータス

保留中。既存テストが他 agent により変更中のため、安定してから Phase 1 に着手する。
