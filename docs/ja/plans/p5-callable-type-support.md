# P5: Callable 型サポート（func ノードの型付与 + 高階関数型推論）

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-CALLABLE-TYPE`

## 背景

- EAST3 の Call ノードの `resolved_type` は正しく設定されるが、`func` ノード（関数名/属性アクセスの式）の `resolved_type` は `unknown` のまま残る。
- 現行の型システムは `callable[float64]`（戻り値のみ）の簡易形しかサポートしていない。
- 現時点では emitter は `Call.resolved_type` で十分動作するが、高階関数（関数を引数として渡すパターン）のサポートにはフル callable 型が必要。

## 目的

- `func` ノードに callable 型を付与し、EAST3 の型情報の網羅性を向上させる。
- 高階関数パターン（`def apply(f: Callable[[int], int], x: int) -> int`）で `f(x)` の戻り値型を推論できるようにする。

## 非対象

- ラムダ式 / クロージャの型推論（将来拡張）
- ジェネリック callable（`Callable[[T], T]`）の型パラメータ推論

## 段階構成

### フェーズ 1: 既知関数の func.resolved_type 設定

既存の型情報（`_lookup_builtin_method_return`、`lookup_stdlib_function_return_type`、`fn_return_types`）を流用し、func ノードに `callable[戻り値型]` を設定する。

対象:
- builtin 関数: `len` → `callable[int64]`、`str` → `callable[str]`、`print` → `callable[None]`
- stdlib 関数: `math.sqrt` → `callable[float64]`、`perf_counter` → `callable[float64]`
- user-defined 関数: `fn_return_types` から `callable[戻り値型]` を構築

変更箇所:
- `core_expr_primary.py` の Name 解決: 関数名の場合に `callable[ret]` を設定
- `core_expr_attr_call_annotation.py` の Attribute 解決: メソッド/モジュール関数の場合に設定

影響:
- `func.resolved_type` が `unknown` → `callable[X]` に変わる
- emitter への影響なし（emitter は `Call.resolved_type` を使い、`func.resolved_type` は参照しない）

### フェーズ 2: TypeExpr への CallableType 追加

EAST の `TypeExpr` スキーマに `CallableType` kind を追加し、引数型 + 戻り値型のフル表現を持つ。

スキーマ:
```json
{
  "kind": "CallableType",
  "params": [
    {"kind": "NamedType", "name": "float64"},
    {"kind": "NamedType", "name": "float64"}
  ],
  "return_type": {"kind": "NamedType", "name": "float64"}
}
```

対象:
- `spec-east.md` §6.3 の TypeExpr schema に `CallableType` を追加
- `type_expr.py` に `CallableType` の正規化・比較ロジックを追加
- フェーズ 1 の `callable[ret]` 簡易形を `CallableType` に置換

変更箇所:
- `docs/ja/spec/spec-east.md` §6.3: `CallableType` kind の仕様追加
- `src/toolchain/frontends/type_expr.py`: `CallableType` のパース・正規化
- `src/toolchain/compile/core_expr_resolution_semantics.py`: user-defined 関数の `arg_types` + `return_type` から `CallableType` を構築

### フェーズ 3: 高階関数の型推論

callable 型の変数を通じた間接呼び出し（`f(x)` where `f: Callable[[int], int]`）で、Call ノードの `resolved_type` を callable の戻り値型から導出する。

対象:
```python
from typing import Callable

def apply(f: Callable[[int], int], x: int) -> int:
    return f(x)  # f(x) の resolved_type = int64
```

変更箇所:
- `core_expr_callee_call_annotation.py`: Name callee が callable 型の変数の場合、`CallableType.return_type` を Call の戻り値型に設定
- `core_stmt_parser.py`: `Callable[[T1, T2], R]` 型注釈のパース
- `core_type_semantics.py`: `Callable` 型の正規化

前提条件:
- フェーズ 2 の `CallableType` スキーマが完成していること
- `Callable` 型注釈のパースが実装されていること

## 受け入れ基準

### フェーズ 1
- builtin / stdlib / user-defined 関数の `func.resolved_type` が `callable[戻り値型]` になる
- 既存テストに回帰がない

### フェーズ 2
- `TypeExpr` に `CallableType` が追加され、フェーズ 1 の簡易形を置換
- EAST spec に `CallableType` が文書化される

### フェーズ 3
- `f: Callable[[int], int]` の変数を通じた `f(x)` で `Call.resolved_type = int64` が設定される
- 高階関数パターンのテスト fixture が追加される

## 決定ログ

- 2026-03-23: Julia 担当から `func.resolved_type: unknown` の報告を受け、callable 型サポートの計画を P5 として起票。現時点では `Call.resolved_type` で emitter は動作するため、高階関数サポートが必要になるまで着手しない方針。
