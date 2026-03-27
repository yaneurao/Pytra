<a href="../../en/spec/spec-any-prohibition.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `Any` アノテーション禁止ガイド

最終更新: 2026-03-18（S6 完了: PyObj 除去）

## 概要

Pytra transpiler は、transpile-target Python コードにおける `Any` 型アノテーションを禁止します。
`Any` アノテーションが検出された場合、`AnyAnnotationProhibitionPass` がコンパイルエラーを出して停止します。

## なぜ `Any` を禁止するか

1. `Any` アノテーションは C++ emitter において型不明な変数を生成します。`PyObj` boxing 階層は S6 で除去済みであり、`object` は現在 `rc<RcObject>`（参照カウント基底）として再定義されていますが、`Any` を使うとその型に対する boxing が試みられ、コンパイルエラーになります。
2. Pytra の型システムは型確定を要求する設計であり、`Any` は型推論を無効化します。
3. `Any` を排除することで、静的型安全な C++ コードを生成できます。

## エラーメッセージ

```
AnyAnnotationProhibitionPass: `Any` type annotations are prohibited.
Use a concrete type (e.g. `str`, `int`, `list[str]`), a union type
(e.g. `str | int`), or a user-defined class instead of `Any`.
Violations:
  [line N, col C] parameter `x` of `foo`: annotation `Any` contains `Any`
  [line M, col D] variable `val`: annotation `dict[str, Any]` contains `Any`
```

## 移行手順

### 変数アノテーション

```python
# Before (禁止)
x: Any = compute()

# After: 具体型を使う
x: int = compute()

# After: union 型を使う (複数の型が返る場合)
x: str | int | None = compute()
```

### 関数引数

```python
# Before (禁止)
def process(data: Any) -> str:
    ...

# After: 具体型
def process(data: str) -> str:
    ...

# After: union 型
def process(data: str | int) -> str:
    ...

# After: ユーザー定義クラス
def process(data: MyClass) -> str:
    ...
```

### 関数戻り値

```python
# Before (禁止)
def get_value() -> Any:
    ...

# After
def get_value() -> str | int | None:
    ...
```

### コンテナ型

```python
# Before (禁止)
values: dict[str, Any] = {}
items: list[Any] = []

# After: 具体的な要素型
values: dict[str, str] = {}
items: list[int] = []

# After: union 型
values: dict[str, str | int | bool] = {}
```

### extern 変数

```python
# Before (禁止, 現在は object も非推奨)
stderr: object = extern(__s.stderr)

# After (S5-01 完了後): アノテーション省略
stderr = extern(__s.stderr)  # C++ side infers type via auto
```

## `from typing import Any` について

`from typing import Any` のインポート文は禁止されません。インポートは annotation-only no-op として許容されます。
ただし、実際の型アノテーションとして `Any` を使用した場合はエラーになります。

## パスの有効化

`AnyAnnotationProhibitionPass` はデフォルトでは無効です。
明示的に有効化するには:

```
python3 src/pytra-cli.py --target cpp input.py --east3-opt-pass +AnyAnnotationProhibitionPass
```

stdlib（`pytra.std.*`）の `Any` 移行（P5-ANY-ELIM-OBJECT-FREE-01-S2-02）完了後に、
デフォルトの pass リスト（`build_local_only_passes()`）に追加される予定です。

## 関連タスク

- `P5-ANY-ELIM-OBJECT-FREE-01-S2-01`: パス実装
- `P5-ANY-ELIM-OBJECT-FREE-01-S2-02`: stdlib 移行
- `P5-ANY-ELIM-OBJECT-FREE-01-S5-01`: `extern` 変数の透過的処理
