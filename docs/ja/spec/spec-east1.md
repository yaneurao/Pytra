<a href="../../en/spec/spec-east1.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# EAST1 仕様（parse 出力契約）

最終更新: 2026-03-24
ステータス: ドラフト

## 1. 位置づけ

EAST1 は parse 段の出力であり、「Python ソースの構文構造を忠実に保持した、型未解決の IR」である。

```
.py → [parse] → .py.east1 → [resolve] → .east2
       構文解析のみ          型解決 + 正規化
```

- 入力: `.py` ファイル 1 つ
- 出力: `.py.east1`（JSON）
- 拡張子が `.py.east1` であることが「Python 由来」を示す。
- **モジュール単位で完全に独立。他ファイルを参照しない。**

## 2. EAST1 が保持するもの

### 2.1 構文構造

- 全ての文・式ノードを Python の構文どおりに保持する。
- `if __name__ == "__main__":` は `main_guard_body` に分離する。
- 重複定義名・予約名のリネームは行う（`renamed_symbols`）。

### 2.2 型注釈（ソースに書かれたまま）

- 型注釈は **ソースに書かれた形** で保持する。正規化しない。
  - `int` は `int` のまま（`int64` にしない）
  - `float` は `float` のまま（`float64` にしない）
  - `Optional[X]` は `Optional[X]` のまま（`X | None` にしない）
  - `List[int]` は `List[int]` のまま（`list[int64]` にしない）
- 関数の引数型・戻り値型を `arg_types` / `return_type` として保持する（ソースのまま）。
- クラスのフィールド型を保持する（ソースのまま）。

### 2.3 ソース情報

- `source_span`: 全ノードにソース位置（行番号・列番号）を付与する。
- `leading_trivia`: コメント（`# ...`）と空行を保持する。
- `repr`: 式の Python ソーステキストを保持する。

### 2.4 import 情報

- `meta.import_bindings`: import 文から抽出した束縛情報。
- `meta.import_modules`: `import module [as alias]` の束縛。
- `meta.import_symbols`: `from module import symbol [as alias]` の束縛。
- import の構文的な情報のみ。runtime 解決（`runtime_module_id` 等）は行わない。

### 2.5 クラス・関数の事前収集

- クラス名、継承関係（単一継承）を収集する。
- 関数名、引数リスト、decorator を収集する。
- ただし型の解決・正規化は行わない（ソースに書かれた型注釈をそのまま保持）。

## 3. EAST1 が保持しないもの（resolve の責務）

以下は EAST1 に含めない。全て resolve 段（EAST2）で処理する。

| フィールド / 処理 | EAST1 | EAST2 (resolve) |
|---|---|---|
| `resolved_type`（式の型） | なし or `"unknown"` | 全式で確定 |
| 型注釈の正規化（`int`→`int64`） | しない | する |
| `Optional[X]` → `X \| None` | しない | する |
| `range()` → `ForRange` | しない | する |
| `casts`（型昇格 cast） | 空リスト `[]` | 挿入済み |
| `runtime_module_id` | なし | 付与 |
| `runtime_symbol` | なし | 付与 |
| `semantic_tag` | なし | 付与 |
| `runtime_call` / `resolved_runtime_call` | なし | 付与 |
| `lowered_kind: "BuiltinCall"` | なし | 付与 |
| `arg_usage`（readonly/reassigned） | なし | 付与 |
| `yields_dynamic` | なし | 付与 |
| cross-module 型解決 | しない | する |
| built-in 関数の型情報 | 参照しない | `built_in.py.east1` から取得 |

## 4. トップレベル構造

```json
{
  "kind": "Module",
  "east_stage": 1,
  "source_path": "input.py",
  "source_span": {...},
  "body": [...],
  "main_guard_body": [...],
  "renamed_symbols": {...},
  "meta": {
    "import_bindings": [...],
    "import_modules": {...},
    "import_symbols": {...}
  }
}
```

- `east_stage`: 常に `1`
- `schema_version`: なし（EAST2 で付与）
- `meta.dispatch_mode`: なし（EAST2 で付与）

## 5. 式ノードの属性

EAST1 の式ノードは以下を持つ:

- `kind`: ノード種別
- `source_span`: ソース位置
- `repr`: Python ソーステキスト
- `borrow_kind`: `"value"`（EAST1 ではデフォルト値のみ）
- `casts`: `[]`（空リスト。EAST1 では cast を挿入しない）

以下は **持たない**（resolve で付与）:

- `resolved_type`
- `type_expr`
- `runtime_module_id` / `runtime_symbol` / `semantic_tag`
- `runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`
- `lowered_kind`
- `yields_dynamic`

## 6. 文ノードの属性

### FunctionDef

- `name`, `original_name`: 関数名（リネーム前後）
- `args`: 引数リスト（ソースの型注釈をそのまま保持）
- `arg_types`: ソースの型注釈文字列リスト（未正規化）
- `return_type`: ソースの戻り値型注釈（未正規化）
- `body`: 関数本体
- `decorators`: decorator 文字列リスト
- `source_span`

持たない: `arg_usage`, `arg_type_exprs`, `return_type_expr`, `meta.runtime_abi_v1`, `meta.template_v1`

### ClassDef

- `name`, `original_name`: クラス名
- `bases`: 基底クラスリスト
- `body`: クラス本体
- `decorators`: decorator 文字列リスト
- `source_span`

持たない: `meta.nominal_adt_v1`

### Assign / AnnAssign

- `target`: 代入先
- `value`: 代入値
- AnnAssign の場合: `annotation`（ソースの型注釈、未正規化）
- `source_span`

持たない: `meta.extern_var_v1`, `decl_type`（resolve で付与）

## 7. 不変条件

1. `east_stage == 1`
2. 他モジュールの情報を参照していない（完全にモジュール独立）
3. 型注釈がソースのまま保持されている（正規化されていない）
4. `resolved_type` が存在しない、または全て `"unknown"`
5. `casts` が全て空リスト
6. `runtime_module_id` / `runtime_symbol` / `semantic_tag` が存在しない
7. `range()` が生の `Call` として残っている（`ForRange` に変換されていない）

## 8. 検証方法

- fixture 132 件 + sample 18 件の golden file と一致すること
- 不変条件を静的に検証する validator を実装すること
  - `resolved_type` 残存チェック（`"unknown"` 以外があればエラー）
  - `runtime_module_id` / `semantic_tag` 残存チェック
  - `casts` 非空チェック
