<a href="../../en/tutorial/python-differences.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Python との違い

Pytra は Python の構文で書けますが、静的型付けが前提のため、Python のすべての書き方が使えるわけではありません。このページでは、Python ユーザーが最初に引っかかるポイントを具体例で説明します。

## 型注釈を書く

Python では型注釈は任意ですが、Pytra では関数の引数と戻り値に型注釈が必要です。

```python
# NG: 型注釈がない
def add(a, b):
    return a + b

# OK: 型注釈がある
def add(a: int, b: int) -> int:
    return a + b
```

変数はリテラルから推論できるので省略可能です。

```python
x = 42          # OK: int に推論される
name = "hello"  # OK: str に推論される

items: list[int] = []  # 空コンテナは注釈が必要
```

## import は `pytra.std.*` を使う

Python 標準ライブラリは直接 import できません。代わりに `pytra.std.*` の shim を使います。

```python
# NG: Python 標準ライブラリの直接 import
import json
import math
import os

# OK: pytra.std 経由で import
from pytra.std import json
from pytra.std import math
from pytra.std.time import perf_counter
from pytra.std.pathlib import Path
```

使えるモジュールの一覧は [pylib モジュール一覧](../spec/spec-pylib-modules.md) を参照してください。

例外: `typing` と `dataclasses` は注釈・デコレータ専用として直接 import できます。

```python
from typing import Optional    # OK
from dataclasses import field  # OK
```

## 整数は多倍長ではない

Python の `int` は任意精度ですが、Pytra では `int64`（64bit 符号付き整数）に変換されます。

```python
# Python: 巨大な整数も扱える
x = 2 ** 100  # OK in Python

# Pytra: int64 の範囲（-2^63 ~ 2^63-1）を超えるとオーバーフロー
x = 2 ** 100  # ⚠ オーバーフローの可能性
```

必要に応じて整数型を明示できます。

```python
small: int8 = 127       # -128 ~ 127
pixel: uint8 = 255      # 0 ~ 255
counter: int32 = 0      # -2^31 ~ 2^31-1
big: int64 = 0          # -2^63 ~ 2^63-1（既定）
```

## `if __name__ == "__main__":` が必要

Pytra ではエントリポイントとして `if __name__ == "__main__":` ブロックが必要です。

```python
# NG: トップレベルに直接書く
print("hello")

# OK: main ガードの中に書く
if __name__ == "__main__":
    print("hello")
```

## 多重継承はできない

Python では複数のクラスを継承できますが、Pytra は単一継承のみです。

```python
# NG: 多重継承
class C(A, B):
    pass

# OK: 単一継承 + trait
class C(A):
    @implements(Drawable)
    def draw(self) -> None: ...
```

複数の振る舞いを持たせたい場合は [Trait](./trait.md) を使ってください。

## `object` / `Any` に対してメソッドを呼べない

Pytra は静的型付けなので、型が不明な値に対してメソッドを呼ぶことはできません。

```python
# NG: object に対するメソッド呼び出し
def process(x: object) -> None:
    x.do_something()  # コンパイルエラー

# OK: 具体的な型で受け取る
def process(x: MyClass) -> None:
    x.do_something()  # OK
```

union 型の場合は `isinstance` で型を絞り込んでから使います。詳しくは [Union 型とナローイング](./union-and-narrowing.md) を参照してください。

## `dict` / `list` は型注釈が必要な場合がある

空のコンテナを作るときは型注釈が必要です。

```python
# NG: 空コンテナの型が推論できない
items = []
data = {}

# OK: 型注釈をつける
items: list[int] = []
data: dict[str, int] = {}
```

中身があれば推論されます。

```python
items = [1, 2, 3]           # OK: list[int] に推論
data = {"a": 1, "b": 2}     # OK: dict[str, int] に推論
```

## `*args` は型注釈が必要

```python
# NG: 型注釈なし
def f(*args):
    pass

# OK: 型注釈あり
def f(*args: int) -> None:
    pass
```

`**kwargs` は使えません。

## 使えない構文

| 構文 | 状態 |
|---|---|
| `**kwargs` | 使えない |
| `async` / `await` | 使えない |
| `with` 文 | 使える |
| `lambda` | 使える |
| リスト内包表記 | 使える（単一ジェネレータのみ） |
| `for/else` | 使えない |
| `while/else` | 使えない |
| デコレータ | `@property`, `@staticmethod`, `@trait`, `@implements`, `@extern`, `@abi`, `@template` が使える |
| `global` / `nonlocal` | 使えない |
| `yield` / ジェネレータ | 使えない |

## もっと詳しく

網羅的な対応表は [Python 互換性ガイド（仕様書）](../spec/spec-python-compat.md) を参照してください。
