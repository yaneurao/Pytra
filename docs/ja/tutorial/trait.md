<a href="../../en/tutorial/trait.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Trait（インターフェース）

このページでは、Pytra の **trait**（インターフェース）の使い方を説明します。trait を使うと、単一継承の制約を維持しつつ、1つの型に複数の振る舞い契約を付与できます。

## trait とは

クラスの継承は 1 つしかできませんが、「描画できる」「シリアライズできる」といった振る舞いを複数のクラスに横断的に求めたい場面があります。trait はそのための仕組みです。

Rust の trait、Java の interface、Swift の protocol に相当します。

## trait の定義

`@trait` デコレータを付けた class 文で定義します。本体にはメソッドのシグネチャだけを書きます。

```python
@trait
class Drawable:
    def draw(self) -> None: ...
    def area(self) -> float: ...

@trait
class Serializable:
    def serialize(self) -> str: ...
```

trait はメソッドの「契約」だけを定義します。実装（メソッドの中身）は書きません。

## trait の実装

クラスが trait を実装するには、`@implements` デコレータで宣言します。

```python
class Circle(Shape):
    @implements(Drawable, Serializable)

    radius: float

    def __init__(self, r: float) -> None:
        self.radius = r

    def draw(self) -> None:
        print("drawing circle with radius " + str(self.radius))

    def area(self) -> float:
        return 3.14 * self.radius * self.radius

    def serialize(self) -> str:
        return "circle:" + str(self.radius)
```

ポイント:

- `Circle(Shape)` で Shape を継承（単一継承はそのまま）
- `@implements(Drawable, Serializable)` で 2 つの trait を実装
- trait で宣言された全メソッドを実装する必要がある。1つでも抜けるとコンパイルエラー

## trait 型で受け取る

trait 型を関数の引数に使えます。その trait を実装していれば、どんなクラスでも渡せます。

```python
def render(d: Drawable) -> None:
    d.draw()
    print("area: " + str(d.area()))

c: Circle = Circle(5.0)
render(c)  # OK: Circle は Drawable を実装している
```

`Circle` から `Drawable` への変換（upcast）は自動的に行われます。明示的な cast は不要です。

## 暗黙変換のルール

Pytra では以下の場合に暗黙的な型変換（upcast）ができます。明示的な cast は不要です。

| 変換元 | 変換先 | 条件 |
|---|---|---|
| 子クラス | 親クラス | 継承関係がある（`class Circle(Shape):`） |
| 具象クラス | trait 型 | `@implements` で宣言している |

```python
class Shape:
    pass

@trait
class Drawable:
    def draw(self) -> None: ...

class Circle(Shape):
    @implements(Drawable)
    def draw(self) -> None: ...

c: Circle = Circle()

# 継承による upcast: Circle → Shape
def process_shape(s: Shape) -> None: ...
process_shape(c)  # OK

# trait による upcast: Circle → Drawable
def render(d: Drawable) -> None: ...
render(c)  # OK

# NG: 関係のない型への変換はできない
def bad(x: object) -> None: ...
bad(c)  # object に対するメソッド呼び出しが禁止なので、object で受ける意味がない
```

いずれも compile 時に検証されます。条件を満たさない変換はコンパイルエラーになります。

## trait の型チェックは compile 時

trait を実装しているかどうかは compile 時に検証されます。trait 型で引数を受け取れば、呼び出し側で型が合わなければコンパイルエラーになります。

```python
def render(d: Drawable) -> None:
    d.draw()  # OK: d は Drawable と型付けされている

c: Circle = Circle(5.0)
render(c)  # OK: Circle は Drawable を実装している

s: Square = Square()  # Square は Drawable を実装していない
render(s)  # コンパイルエラー: Square は Drawable を実装していない
```

runtime で「この値は trait を実装しているか」を `isinstance` で問う必要はありません。型注釈で trait を指定すれば、compile 時に安全が保証されます。

## 複数のクラスが同じ trait を実装する

trait の価値は、異なるクラスに共通の振る舞いを定義できることです。

```python
@trait
class Serializable:
    def serialize(self) -> str: ...

class Circle(Shape):
    @implements(Serializable)
    def serialize(self) -> str:
        return "circle:" + str(self.radius)

class Rectangle(Shape):
    @implements(Serializable)
    def serialize(self) -> str:
        return "rect:" + str(self.width) + "x" + str(self.height)

def save_all(items: list[Serializable]) -> None:
    for item in items:
        print(item.serialize())
```

`Circle` と `Rectangle` は異なるクラスですが、どちらも `Serializable` を実装しているので、`list[Serializable]` に入れて統一的に扱えます。

## trait の継承

trait は他の trait を継承できます。

```python
@trait
class Printable:
    def to_string(self) -> str: ...

@trait
class DebugPrintable(Printable):
    def debug_string(self) -> str: ...
```

`DebugPrintable` を実装するクラスは、`to_string` と `debug_string` の両方を実装する必要があります。

## 制約

- trait にはフィールド（データ属性）を書けない
- trait にはメソッドの実装（本体）を書けない（シグネチャのみ）
- trait はインスタンス化できない（`Drawable()` はエラー）
- `@implements` で宣言した trait の全メソッドを実装しないとコンパイルエラー
- `object` / `Any` 型の変数に対して trait のメソッドを呼ぶことはできない。`object` を trait 型の引数に渡すこともできない（`object` は trait を implements していない）。trait を使いたいなら、最初から trait 型で受け取ること

```python
# NG: object に対して trait メソッドは呼べない
def bad(x: object) -> None:
    x.draw()  # コンパイルエラー: object にメソッド呼び出しは禁止

# NG: object を trait 型に渡すこともできない
def render(d: Drawable) -> None:
    d.draw()

x: object = Circle(5.0)
render(x)  # コンパイルエラー: object は Drawable を implements していない

# OK: 型が分かっている変数なら渡せる
c: Circle = Circle(5.0)
render(c)  # OK: Circle は Drawable を implements している
```

## trait vs 継承の使い分け

| 使いたい場面 | 使うもの |
|---|---|
| 「AはBの一種である」（is-a） | クラス継承（`class Dog(Animal):`） |
| 「Aはこの振る舞いができる」（can-do） | trait（`@implements(Drawable)`） |
| データ（フィールド）を共有したい | クラス継承 |
| 複数の契約を同時に満たしたい | trait（複数指定可） |

## まとめ

| やりたいこと | 書き方 |
|---|---|
| trait を定義する | `@trait class A: def method(self) -> T: ...` |
| trait を実装する | `@implements(A, B)` をクラスに付ける |
| trait 型で受け取る | `def f(x: A) -> None:` |
| 型チェック | compile 時に自動検証（runtime の isinstance 不要） |

詳しい仕様は以下を参照してください:
- [Trait 仕様](../spec/spec-trait.md) — 各言語への写像規則、EAST 表現、検証ルール
