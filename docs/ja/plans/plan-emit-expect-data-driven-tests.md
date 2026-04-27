# 計画: パイプライン系テストのデータ駆動化 (P20-DATA-DRIVEN-TESTS)

## 背景

`tools/unittest/` に 267 個のテストスクリプトがある。このうち約 80 件は「Python ソース or EAST JSON を入力 → パイプライン実行 → 出力文字列 or JSON の一部一致を検証」というパターンで、Python コードで書く必要がない。

対象:
- `tools/unittest/ir/` — EAST パーサー / lowering テスト (~30件)
- `tools/unittest/toolchain2/` — renderer / narrowing テスト (~18件)
- `tools/unittest/emit/<lang>/test_py2*_smoke.py` — 言語別 smoke (~20件)
- `tools/unittest/common/test_pylib_*.py` — pylib テスト (~10件)

対象外（Python テストとして残す）:
- `tools/unittest/tooling/` (92件) — CLI 契約テスト、ファイルレイアウト検証、manifest 検証。ファイルシステムの状態やプロセス実行を検証するもので、入力→出力パターンに載らない
- `tools/unittest/selfhost/` (12件) — selfhost ビルド、golden 比較、stage2 diff。プロセス実行とファイル比較が主体
- `tools/unittest/link/` (5件) — linker のグラフ解析、export 解決。複数モジュールの関係をテスト
- `tools/unittest/common/` の一部 — backend registry メタデータ整合性、runtime symbol index 構造検証

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

### Python テストとして残すもの (~190件)

以下は JSON では表現しにくいため、`tools/unittest/` に Python テストとして残す:

- `tools/unittest/tooling/` — CLI 契約、ファイルレイアウト、manifest 検証 (92件)
- `tools/unittest/selfhost/` — selfhost ビルド、golden 比較 (12件)
- `tools/unittest/link/` — linker グラフ解析、export 解決 (5件)
- `tools/unittest/common/` の構造検証系 — backend registry、runtime symbol index 等
- emitter コンテキスト（EmitContext）のカスタマイズが必要なテスト
- 複数ファイル間の import 解決テスト

## 移行計画

### Phase 1: emit 層で方式を確立

1. `test/cases/emit/cpp/` に JSON テストケース 5〜10 件を作成
2. `tools/unittest/test_emit_cases.py` を実装
3. `test_common_renderer.py` の対応テストを JSON に移行し、元メソッドを削除
4. 動作確認

### Phase 2: パイプライン層に横展開

1. `test/cases/{east1,east2,east3}/` に JSON テストケースを作成（isinstance narrowing, closure capture 等）
2. `tools/unittest/test_pipeline_cases.py` を実装
3. `tools/unittest/ir/` と `tools/unittest/toolchain2/` の対応テストを段階的に JSON に移行

### Phase 3: smoke テストの統合

1. `tools/unittest/emit/<lang>/test_py2*_smoke.py` (~20件) を `test/cases/emit/<lang>/` の module レベル JSON に移行
2. `tools/unittest/common/test_pylib_*.py` (~10件) を `test/cases/east2/` or `east3/` に移行
3. 空になったスクリプトを削除

### Phase 3 完了後の姿

```
test/cases/           # ~80件の JSON テストケース（データ駆動）
  east1/
  east2/
  east3/
  emit/{cpp,go,rs,...}/

tools/unittest/       # ~190件の Python テスト（残存）
  test_emit_cases.py      # JSON テストランナー (emit)
  test_pipeline_cases.py  # JSON テストランナー (pipeline)
  tooling/                # CLI・manifest 契約テスト (残存)
  selfhost/               # selfhost テスト (残存)
  link/                   # linker テスト (残存)
  common/                 # 構造検証系 (残存)
  emit/cpp/               # EmitContext カスタマイズ系のみ残存
  ir/                     # JSON 移行できなかった複雑テストのみ残存
```

## 利点

- パイプライン系テスト (~80件) のケース追加が JSON ファイル追加のみ（Python コード変更不要）
- テストケースの一覧性が高い（ファイル名で内容がわかる）
- 言語横断で同じ仕組みを使える（smoke テスト 20件が JSON に統合）
- agent がテストを追加するときに既存スクリプトを読む必要がない
- ツール/CI 系テスト (~190件) は Python テストとして残し、無理に JSON 化しない

## ステータス

Phase 1 / Phase 2 完了。Phase 3 は smoke 統合が継続中で、pylib 統合は完了。

- 2026-04-27: [ID: P20-DDT-S1] `test/cases/emit/cpp/` に C++ expr レベル JSON ケース 8 件を追加。
- 2026-04-27: [ID: P20-DDT-S2] `tools/unittest/test_emit_cases.py` を追加。`pytest` がある環境では parametrize、最小ローカル環境では `unittest` fallback で同じ JSON ケースを実行する。
- 2026-04-27: [ID: P20-DDT-S3] `tools/unittest/toolchain2/test_common_renderer.py` から対応する C++ expr 期待値テスト 8 件を削除し、JSON ケースへ移行。
- 2026-04-27: [ID: P20-DDT-S4] `test/cases/{east1,east2,east3}/` に pipeline JSON ケース 6 件を追加。
- 2026-04-27: [ID: P20-DDT-S5] `tools/unittest/test_pipeline_cases.py` を追加。ソース文字列から EAST1/EAST2/EAST3 を in-memory で生成し、JSON path assertion を評価する。
- 2026-04-27: [ID: P20-DDT-S6] `tools/unittest/ir/test_east_core_parser_behavior_exprs.py` と `tools/unittest/toolchain2/test_tuple_unpack_lowering_profile.py` から対応テスト 2 件を JSON ケースへ移行。
- 2026-04-27: [ID: P20-DDT-S7] `bitwise_invert_basic` smoke を `cpp` / `dart` / `go` / `js` / `julia` / `kotlin` / `lua` / `nim` / `php` / `powershell` / `rb` / `rs` / `scala` / `swift` / `ts` の JSON ケースへ移動し、`test_emit_cases.py` に module-level fixture emit の target 対応を追加。
- 2026-04-27: [ID: P20-DDT-S7] 壊れていた `tools/unittest/emit/dart/test_py2dart_smoke.py` の fixture smoke を `test/cases/emit/dart/` へ移行し、空になったスクリプトを削除。
- 2026-04-27: [ID: P20-DDT-S7] `tools/unittest/emit/test_py2starred_smoke.py` の all-target starred tuple fixture smoke を `test/cases/emit/<lang>/starred_call_tuple_basic.json` へ移行し、スクリプトを削除。
- 2026-04-27: [ID: P20-DDT-S7] Nim の `for_range` fixture smoke を `test/cases/emit/nim/for_range.json` へ移行。
- 2026-04-27: [ID: P20-DDT-S7] PowerShell の `bitwise_invert_basic` ヘッダー確認を既存 JSON ケースへ統合。
- 2026-04-27: [ID: P20-DDT-S7] `go` / `java` / `kotlin` / `rb` / `scala` / `swift` の `inheritance` skeleton smoke を JSON ケースへ移行。
- 2026-04-27: [ID: P20-DDT-S8] `argparse` / `dataclasses` / `enum` / `re` / `sys` / `typing` / `json` / `path` / `os_glob` の pylib テストを `test/cases/pylib/` へ移行し、`tools/unittest/test_pylib_cases.py` へ集約。
- 2026-04-27: [ID: P20-DDT-S9] 空になった `tools/unittest/common/test_pylib_*.py` を削除。
