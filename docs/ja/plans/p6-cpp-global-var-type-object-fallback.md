# P6: グローバル変数型推論失敗の object フォールバック排除

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-GLOBAL-VAR-TYPE-OBJECT-FALLBACK-01`

## 背景

`module.py` の `_collect_module_global_var_type()` が、
モジュールレベルのグローバル変数の型を推論できない場合に `object` にフォールバックしている。

| ファイル | 行 | 関数 | 条件 |
|---|---|---|---|
| `src/toolchain/emit/cpp/emitter/module.py` | L1155 | `_collect_module_global_var_type()` | アノテーションも RHS 型も空の場合 |

```python
# 現状（L1155）:
picked = picked if picked != "" else "object"
```

## 方針

- グローバル変数に型注釈がなく RHS からも型が推論できない場合は、
  コンパイルエラーとして Python ソース側に明示型注釈を要求する。
- 特に定数（`ALL_CAPS` 変数）は初期化式から型が自明なことが多い。
  リテラル型推論（`"str"` → `str`、`42` → `int64` 等）を優先適用する。

## 対象

- `src/toolchain/emit/cpp/emitter/module.py` L1155

## 受け入れ基準

- グローバル変数型推論失敗によるサイレント `object` フォールバックが 0 になる。
- selfhost mismatches=0。

## 決定ログ

- 2026-03-18: object 排除方針の下、カテゴリ B フォールバックとして特定。
