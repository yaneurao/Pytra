# EAST2 仕様（resolve 出力契約）

最終更新: 2026-03-24
ステータス: ドラフト

## 1. 位置づけ

EAST2 は resolve 段の出力であり、「言語固有の意味論が除去された、型解決済みの正規化 IR」である。

```
.py → [parse] → .py.east1 → [resolve] → .east2 → [compile] → .east3
                  Python 固有         言語非依存
```

- 入力: `.py.east1`（Python 固有の EAST1）
- 出力: `.east2`（言語非依存）
- 拡張子から `.py` が消えることが「Python の意味論が抜けた」ことを示す。

## 2. EAST1 との差分（resolve が行うこと）

### 2.1 型解決

- 全ての式ノードに `resolved_type` が確定している。`unknown` はゼロ。
- `type_expr`（構造化型表現）が全ての型注釈付きノードに付与されている。
- `type_expr` と `resolved_type` が両方ある場合、`type_expr` が正本。矛盾は `semantic_conflict` で fail-closed。
- cross-module 型解決: import 先モジュールの FunctionDef から戻り値型・引数型を取得。ハードコードテーブル（signature_registry 等）に依存しない。

### 2.2 型注釈の正規化

| Python 表記 | EAST2 正規型 |
|---|---|
| `int` | `int64` |
| `float` | `float64` |
| `byte` | `uint8` |
| `bytes` / `bytearray` | `list[uint8]` |
| `pathlib.Path` | `Path` |
| `any` / `object` | `Any` |
| `Optional[X]` | `X \| None` → `OptionalType(inner=X)` |
| `Union[X, Y]` | `X \| Y` → `UnionType` or `OptionalType` |

### 2.3 構文正規化

- `for x in range(...)` → `ForRange`（`start/stop/step/range_mode` を保持）
- 式位置の `range(...)` → `RangeExpr`（`ListComp` 含む）
- `range()` が生の `Call` として残ることは禁止。resolve の不備として扱う。
- `if __name__ == "__main__":` → `main_guard_body` に分離（EAST1 で実施済み、維持）
- `from __future__ import annotations` は受理するが EAST2 ノードには出力しない。

### 2.4 型推論

- `Name`: 型環境から解決。未解決は `inference_failure` で fail-closed。
- `Constant`: 整数→`int64`、実数→`float64`、真偽→`bool`、文字列→`str`、`None`
- `List/Set/Dict`: 非空は要素型単一化、空は注釈から採用。注釈なし空コンテナは `inference_failure`。
- `Tuple`: `tuple[T1, T2, ...]`
- `BinOp`: 数値演算の型昇格、`Path / str` → `Path`、`str * int` → `str` 等
- `Subscript`: `list[T][i]` → `T`、`dict[K,V][k]` → `V`、`str[i]` → `str`
- `Call`: 関数の戻り値型から解決。built-in / stdlib / ユーザー定義いずれも EAST1 の FunctionDef ノードから取得。
- `ListComp`: 単一ジェネレータのみ対応。

### 2.5 cast 挿入

- 数値型の混在演算で自動昇格 cast を挿入する。
  - int-float 混在: `int64 + float64` → 左辺に `cast(int64 → float64)` を付与
  - int 同士のサイズ違い: `uint8 ^ int64` → `uint8` 側に `cast(uint8 → int64)` を付与
  - 昇格ルールは **C++ の integer promotion / usual arithmetic conversion に準ずる**:
    - 両辺のランク（型サイズ）が異なる場合、小さい方を大きい方に昇格
    - 同ランクで符号が異なる場合（`uint16 ^ int16` 等）、符号なし側に統一
- stdlib 関数の引数型が `float64` の場合、`int64` 引数に `numeric_promotion` cast を挿入する。
  - 例: `math.sqrt(x)` (x: int64) → arg[0] に `cast(int64 → float64)`
- cast は式ノードの `casts` リストに付与する:
  ```json
  {"on": "left|right|body", "from": "int64", "to": "float64", "reason": "numeric_promotion"}
  ```

### 2.6 import 解決

- `meta.import_bindings`: import の正本リスト（`ImportBinding[]`）
- `meta.qualified_symbol_refs`: `from-import` の解決済み参照
- `meta.import_modules`: `import module [as alias]` の束縛情報
- `meta.import_symbols`: `from module import symbol [as alias]` の束縛情報
- built-in 関数（`len`, `print`, `str` 等）は `built_in.py` の EAST1 から解決。ハードコードしない。

### 2.7 runtime binding 解決

- import モジュール属性呼び出し（`math.sqrt` 等）に以下を付与:
  - `runtime_module_id`: `"pytra.std.math"`
  - `runtime_symbol`: `"sqrt"`
  - `semantic_tag`: `"stdlib.method.sqrt"`
  - `resolved_runtime_call`: `"math.sqrt"`
- built-in 呼び出し（`len`, `print` 等）に以下を付与:
  - `runtime_module_id`: `"pytra.built_in.sequence"` 等
  - `runtime_symbol`: `"len"` 等
  - `semantic_tag`: `"core.len"` 等

## 3. トップレベル構造

```json
{
  "kind": "Module",
  "east_stage": 2,
  "schema_version": 1,
  "source_path": "...",
  "body": [...],
  "main_guard_body": [...],
  "renamed_symbols": {...},
  "meta": {
    "import_bindings": [...],
    "qualified_symbol_refs": [...],
    "import_modules": {...},
    "import_symbols": {...},
    "dispatch_mode": "native | type_id"
  }
}
```

- `east_stage`: 常に `2`
- `schema_version`: 常に `1`
- `meta.dispatch_mode`: コンパイル方針値。意味適用は EAST2→EAST3 の 1 回のみ。

## 4. ノード共通属性

式ノード（`_expr`）は以下を持つ:

- `kind`, `source_span`, `resolved_type`, `type_expr`, `borrow_kind`, `casts`, `repr`
- `resolved_type`: 全ノードで確定済み（`unknown` 禁止）
- `type_expr`: 構造化型表現（`resolved_type` より優先）
- `borrow_kind`: `value | readonly_ref | mutable_ref`
- `casts`: 数値昇格等の cast リスト

## 5. EAST2 で保持しないもの

以下は EAST3（compile 段）の責務であり、EAST2 には含めない:

- boxing/unboxing 命令（`ObjBox`, `ObjUnbox` 等）
- `type_id` 判定命令
- `ForCore` / `iter_plan`（反復計画の命令化）
- `dispatch_mode` の意味適用結果
- whole-program 解析結果（call graph, escape 解析, container ownership）

## 6. 不変条件

1. `east_stage == 2`
2. 全式ノードの `resolved_type` が確定（`unknown` はゼロ）
3. `range()` が生の `Call` として残っていない
4. `int` / `float` 等の Python 型名が正規化済み（`int64` / `float64`）
5. cross-module 型解決がハードコードテーブルに依存していない
6. `type_expr` と `resolved_type` が矛盾していない

## 7. 検証方法

- fixture 132 件 + sample 18 件の golden file と一致すること
- 不変条件を静的に検証する validator を実装すること（`unknown` 残存チェック、`range` Call 残存チェック等）
