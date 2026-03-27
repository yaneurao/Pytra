<a href="../../en/tutorial/union-and-narrowing.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Union 型と isinstance ナローイング

このページでは、Pytra で複数の型を扱う **union 型** と、条件分岐で型を絞り込む **isinstance ナローイング** の使い方を説明します。

## Union 型とは

Python の変数は通常 1 つの型を持ちますが、「この変数は int か str のどちらかが入る」という場面があります。Pytra では `type` 文で union 型を宣言できます。

```python
type Result = int | str | None
```

これは「`Result` 型の変数には `int`、`str`、`None` のいずれかが入る」という意味です。

### 実例: JSON パーサー

JSON の値は数値・文字列・真偽値・null・配列・オブジェクトのいずれかです。Pytra ではこれを 1 つの union 型で表現します。

```python
type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
```

再帰的な定義（`list[JsonVal]` の中に `JsonVal` 自身が含まれる）も使えます。

### Optional 型

「値があるか None か」の 2 択は `Optional` で書けます。

```python
from typing import Optional

def find(items: list[str], key: str) -> Optional[str]:
    for item in items:
        if item == key:
            return item
    return None
```

内部的には `Optional[str]` は `str | None` と同じです。

### 三項演算子の型推論

三項演算子（`x if cond else y`）の型は、真側と偽側の型から自動的に推論されます。

両側が同じ型なら、結果もその型です:

```python
# label の型は str に推論される
label = "yes" if flag else "no"
```

片側が `None` の場合は `Optional[T]` になります:

```python
# name の型は str | None に推論される
name = user.get("name") if "name" in user else None
```

両側が異なる型の場合は union 型になります:

```python
# result の型は int | str に推論される
result = parse_int(s) if is_number else parse_str(s)
```

## isinstance で型を判定し、cast で絞り込む

Pytra は静的型付けが前提なので、union 型の変数に対して直接メソッドを呼ぶことはできません。まず `isinstance` で型を判定し、`cast` で具体的な型に変換してからメソッドを呼びます。

```python
from pytra.typing import cast

def process(val: JsonVal) -> None:
    if isinstance(val, dict):
        d: dict[str, JsonVal] = cast(dict[str, JsonVal], val)
        d.get("key")        # OK: d は dict なのでメソッドが使える

    elif isinstance(val, list):
        items: list[JsonVal] = cast(list[JsonVal], val)
        for item in items:   # OK: items は list なのでループできる
            print(item)
```

`cast` は `pytra.typing` からインポートします。実行時には何もしません（型チェッカーへのヒントとして機能します）。

もう少し大きな例:

```python
def describe(val: JsonVal) -> str:
    if isinstance(val, dict):
        d: dict[str, JsonVal] = cast(dict[str, JsonVal], val)
        return "object with " + str(len(d)) + " keys"
    elif isinstance(val, list):
        items: list[JsonVal] = cast(list[JsonVal], val)
        return "array with " + str(len(items)) + " items"
    elif isinstance(val, str):
        return val
    elif isinstance(val, bool):
        if val:
            return "true"
        return "false"
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return str(val)
    return "null"
```

## 自動ナローイング: cast を省略できる

上のコードでは毎回 `cast` を書いていますが、Pytra は `isinstance` の判定結果を見て **if ブロック内の変数の型を自動的に絞り込み**ます。この機能を **isinstance ナローイング** と呼びます。

先ほどのコードは、こう書き直せます:

```python
def process(val: JsonVal) -> None:
    if isinstance(val, dict):
        # val は自動的に dict[str, JsonVal] として扱われる
        val.get("key")      # OK: cast なしでメソッドが使える
        for k, v in val.items():
            print(k)

    elif isinstance(val, list):
        # val は自動的に list[JsonVal] として扱われる
        for item in val:     # OK: cast なしでループできる
            print(item)
```

`isinstance` の直後の if ブロック内では、変数の型が自動的に絞り込まれるので、`cast` なしでそのままメソッド呼び出しやループに使えます。

### ナローイングが効くパターン

#### if/elif

```python
if isinstance(x, int):
    print(x + 1)        # x は int
elif isinstance(x, str):
    print(x.upper())    # x は str
```

#### early return guard

`isinstance` の否定で早期リターンすると、その後の行で型が絞り込まれます。

```python
def process(val: JsonVal) -> str:
    if not isinstance(val, dict):
        return ""
    # ここ以降 val は dict[str, JsonVal]
    return val.get("name")
```

`return` の他に `raise`、`break`、`continue` でも同じ効果があります。

#### 三項演算子

```python
owner_node = owner if isinstance(owner, dict) else None
# owner_node は dict[str, JsonVal] | None として推論される
```

### ナローイングが効かないパターン（cast を使う）

以下のパターンでは自動ナローイングが効きません。`cast` を使ってください。

```python
from pytra.typing import cast

# else ブロック: ナローイングされない
if isinstance(x, dict):
    pass
else:
    # x の型は絞り込まれないので、cast が必要
    s: str = cast(str, x)
```

### 再代入するとナローイングが無効になる

if ブロック内で変数に再代入すると、ナローイングは無効化されます。

```python
if isinstance(val, dict):
    val = other_value    # 再代入した
    # ここでは val は dict としてナローイングされない
```

## POD 型の isinstance

整数型（`int8`, `int16`, `int32`, `int64` 等）や浮動小数型（`float32`, `float64`）は **exact match** で判定されます。値域の包含関係は考慮されません。

```python
x: int16 = 1
print(isinstance(x, int16))   # True  — 同じ型
print(isinstance(x, int8))    # False — 別の型（int8 は int16 の部分型ではない）
print(isinstance(x, int32))   # False — 別の型（値域が含まれていても型が異なる）
```

## まとめ

| やりたいこと | 書き方 |
|---|---|
| union 型を定義する | `type X = A \| B \| C` |
| Optional を使う | `Optional[T]` または `T \| None` |
| 型を判定する | `isinstance(x, T)` |
| 判定後にメソッドを呼ぶ | if ブロック内でそのまま使える（自動ナローイング） |
| ナローイングが効かない場合 | `cast(T, x)` を使う |

詳しい仕様は以下を参照してください:
- [tagged union 仕様](../spec/spec-tagged-union.md) — union 型の定義と各言語へのコード生成規則
- [type_id 仕様 §4.2](../spec/spec-type_id.md) — POD 型とクラス型の isinstance 判定方式
- [EAST 仕様 §7.1](../spec/spec-east.md) — isinstance ナローイングの詳細ルール
