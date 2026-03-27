<a href="../../en/spec/spec-trait.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Trait 仕様（pure interface・多重実装）

最終更新: 2026-03-27
ステータス: ドラフト

## 1. 目的

- Python の単一継承制約を維持しつつ、複数の振る舞い契約を型に付与する仕組みを提供する。
- 各ターゲット言語のネイティブな interface / trait / protocol に写像する。
- `type_id`（単一継承の区間判定）とは独立した `trait_id` 軸で `isinstance` を実現する。

## 2. 非目標

- デフォルト実装（trait にメソッド本体を持たせること）。trait は pure interface とする。
- 構造的部分型（structural subtyping）。trait の実装は名目的（明示宣言）とする。
- trait object のファーストクラスサポート（`Box<dyn T>` 相当の動的 dispatch コンテナ）。

## 3. 構文

### 3.1 trait 宣言

`@trait` デコレータ付きの class 文で宣言する。本体はメソッドシグネチャ（`...` body）のみ。

```python
@trait
class Drawable:
    def draw(self) -> None: ...
    def area(self) -> float: ...

@trait
class Serializable:
    def serialize(self) -> str: ...
```

制約:

- trait はインスタンス化できない。
- trait はフィールド（データ属性）を持てない。
- trait は他の trait を継承できる（trait 継承）。`@trait class A(B):` は B も `@trait` であること。
- trait はクラスを継承できない。
- メソッド本体を持つ（`...` 以外の body）場合は `unsupported_syntax` で fail-closed。

### 3.2 trait 実装

`@implements` デコレータでクラスが実装する trait を宣言する。単一継承とは独立。

```python
class Circle(Shape):
    @implements(Drawable, Serializable)

    def draw(self) -> None:
        print("drawing circle")

    def area(self) -> float:
        return 3.14 * self.radius * self.radius

    def serialize(self) -> str:
        return "circle:" + str(self.radius)
```

制約:

- `@implements` に列挙した全 trait の全メソッドを実装しなければならない。未実装は `semantic_conflict` で fail-closed。
- 1 つのクラスは複数の trait を実装できる。
- `@implements` は `class` 文の直下に 1 回だけ書く。

### 3.3 trait 型の引数

trait 型を関数引数や変数の型注釈に使える。

```python
def render(d: Drawable) -> None:
    d.draw()

c: Circle = Circle()
render(c)  # Circle → Drawable の暗黙 upcast
```

## 4. 型システムとの関係

### 4.1 type_id との分離

- trait は `type_id` を持たない（インスタンス化できない）。
- trait は runtime に情報を持たない。compile 時の型検証のみ。
- 単一継承の `type_id` ツリーは trait によって変更されない。

### 4.2 trait upcast

`@implements(A)` を宣言したクラス X のインスタンスは、`A` 型として暗黙的に使える。

- resolve 段でコンパイル時に「X が A を implements しているか」を検証する。
- 検証 OK なら、明示的な cast は不要。
- EAST3 には trait upcast であることを metadata として保持する。
- emitter は各言語の暗黙 upcast に写像する（大半の言語で追加コード不要）。

### 4.3 isinstance

trait の isinstance は compile 時に resolve が静的に検証する。runtime の判定コードは生成しない。

```python
def f(x: Drawable) -> None:
    x.draw()  # OK: compile 時に Drawable と型付けされている

c: Circle = Circle()
# isinstance(c, Drawable) は resolve が compile 時に True と判定する。
# Pytra では object/Any に対するメソッド呼び出しが禁止されているため、
# runtime で trait を判定する必要がない。
```

## 5. EAST 表現

### 5.1 trait 宣言

`ClassDef` に `meta.trait_v1` を付与する。

```json
{
  "kind": "ClassDef",
  "name": "Drawable",
  "decorators": ["trait"],
  "meta": {
    "trait_v1": {
      "schema_version": 1,
      "methods": [
        {"name": "draw", "args": ["self"], "return_type": "None"},
        {"name": "area", "args": ["self"], "return_type": "float64"}
      ],
      "extends_traits": []
    }
  }
}
```

### 5.2 trait 実装

`ClassDef` に `meta.implements_v1` を付与する。

```json
{
  "kind": "ClassDef",
  "name": "Circle",
  "bases": ["Shape"],
  "decorators": ["implements(Drawable, Serializable)"],
  "meta": {
    "implements_v1": {
      "schema_version": 1,
      "traits": ["Drawable", "Serializable"]
    }
  }
}
```

### 5.3 trait メソッド marker

trait を実装するクラスのメソッドのうち、trait のメソッドを実装しているものには `FunctionDef` に `meta.trait_impl_v1` を付与する。

```json
{
  "kind": "FunctionDef",
  "name": "draw",
  "meta": {
    "trait_impl_v1": {
      "schema_version": 1,
      "trait_name": "Drawable",
      "method_name": "draw"
    }
  }
}
```

- resolve 段で、`@implements` に列挙された trait のメソッドとクラスのメソッドを照合し、一致するものに `trait_impl_v1` を付与する。
- 1 つのメソッドが複数の trait のメソッドを同時に実装する場合（同名メソッドが複数 trait にある場合）は、`trait_impl_v1` をリストとして保持する。
- `trait_impl_v1` がないメソッドは、そのクラス固有のメソッドとして扱う。

emitter はこの marker を見て言語固有の写像を行う:

| 言語 | `trait_impl_v1` ありのメソッド |
|---|---|
| Rust | `impl Drawable for Circle { fn draw(&self) { ... } }` ブロック内に配置 |
| Java / Kotlin | `@Override` アノテーションを付与 |
| C++ | `override` キーワードを付与 |
| Swift | protocol 準拠メソッドとして扱う |
| Go / TS / C# | 追加の修飾なし（言語が自動解決） |

### 5.4 trait upcast

resolve 段で trait upcast を検証済みの箇所には、暗黙 cast として扱い、emitter に追加の判断を要求しない。

## 6. 各言語への写像

### 6.1 trait 宣言

| 言語 | 写像 |
|---|---|
| Java | `interface Drawable { void draw(); float area(); }` |
| C# | `interface IDrawable { void Draw(); float Area(); }` |
| Kotlin | `interface Drawable { fun draw(); fun area(): Double }` |
| Swift | `protocol Drawable { func draw(); func area() -> Double }` |
| Go | `type Drawable interface { Draw(); Area() float64 }` |
| Rust | `trait Drawable { fn draw(&self); fn area(&self) -> f64; }` |
| C++ | `class Drawable { public: virtual void draw() = 0; virtual double area() = 0; virtual ~Drawable() = default; };`（trait 間継承は `virtual` 継承） |
| TS | `interface Drawable { draw(): void; area(): number; }` |

### 6.2 trait 実装

| 言語 | 写像 |
|---|---|
| Java | `class Circle extends Shape implements Drawable, Serializable` |
| C# | `class Circle : Shape, IDrawable, ISerializable` |
| Kotlin | `class Circle : Shape(), Drawable, Serializable` |
| Swift | `class Circle: Shape, Drawable, Serializable` |
| Go | 構造的（明示宣言不要、メソッドを満たせば OK） |
| Rust | `impl Drawable for Circle { ... }` + `impl Serializable for Circle { ... }` |
| C++ | `class Circle : public Shape, virtual public Drawable, virtual public Serializable`（trait は `virtual` 継承） |
| TS | `class Circle extends Shape implements Drawable, Serializable` |

### 6.3 trait upcast（X → A）

| 言語 | 写像 |
|---|---|
| Java / C# / Kotlin / Swift / TS | 暗黙（コンパイラが保証） |
| Go | 暗黙（`var d Drawable = c`） |
| Rust | `&c as &dyn Drawable` or `Box<dyn Drawable>` |
| C++ | `Object<T>` の変換コンストラクタで暗黙変換（§6.4 参照） |

### 6.4 C++ `Object<T>` の trait upcast 対応

C++ では trait を pure virtual class として多重継承し、`Object<T>` にテンプレート変換コンストラクタを追加する。

```cpp
template<typename T>
class Object {
    T* ptr;
    RefCount* rc;
public:
    // U* が T* に変換可能なら暗黙変換を許可
    template<typename U,
             typename = std::enable_if_t<std::is_convertible_v<U*, T*>>>
    Object(const Object<U>& other) : ptr(other.ptr), rc(other.rc) {
        rc->inc();
    }
};
```

これにより `Object<Circle>` → `Object<Drawable>` が暗黙変換になる。

### 6.5 C++ trait 間継承のダイヤモンド問題

trait が他の trait を継承する場合、C++ ではダイヤモンド問題が発生する。

```python
@trait
class Printable:
    def to_string(self) -> str: ...

@trait
class DebugPrintable(Printable):
    def debug_string(self) -> str: ...

@trait
class Loggable(Printable):
    def log(self) -> None: ...

class MyClass(Base):
    @implements(DebugPrintable, Loggable)  # Printable が2経路から来る
```

C++ emitter はこれを **virtual 継承** で解決する:

```cpp
class Printable { public: virtual std::string to_string() = 0; virtual ~Printable() = default; };
class DebugPrintable : virtual public Printable { public: virtual std::string debug_string() = 0; };
class Loggable : virtual public Printable { public: virtual void log() = 0; };

class MyClass : public Base, virtual public DebugPrintable, virtual public Loggable {
    // Printable は1つだけ（virtual 継承により）
    std::string to_string() override { ... }
    std::string debug_string() override { ... }
    void log() override { ... }
};
```

規則:

- trait 間の継承は全て `virtual public` で emit する。
- クラスから trait への implements も `virtual public` で emit する。
- pure interface（フィールドなし、実装なし）なので virtual 継承のオーバーヘッドは最小限。
- trait メソッドの実装には `override` キーワードを付与する（`meta.trait_impl_v1` を参照）。

他の言語（Java, C#, Kotlin, Swift, Go, Rust, TS）は interface の多重実装がネイティブサポートされているため、ダイヤモンド問題は発生しない。

## 7. isinstance と trait

trait の isinstance は **compile 時に resolve が検証するだけ** であり、runtime 判定は不要。

理由:

- Pytra では `object`/`Any` に対するメソッド呼び出しは禁止されている。
- trait 型で引数を受け取れば、compile 時に型が確定する。runtime で「この値は trait を実装しているか」を問う場面がない。
- `isinstance(x, Drawable)` は resolve 段で `x` の型が `Drawable` を `@implements` しているかを静的に検証し、narrowing する。runtime の判定コードは生成しない。

禁止事項:

- runtime に trait_id / trait_bits / trait ビットセットを持たせない。
- ControlBlock / TypeInfo に trait 情報を格納しない。
- linker で trait_id テーブルを生成しない。
- trait は型システム（compile 時）の概念であり、runtime dispatch の概念ではない。

## 8. 検証（resolve 段）

resolve 段で以下を静的に検証する:

1. `@implements` に列挙した全 trait の全メソッドが、クラスに実装されていること。
2. メソッドのシグネチャ（引数型・戻り値型）が trait 宣言と一致すること。
3. trait 型を引数に取る関数に渡される値が、その trait を implements していること。
4. trait 宣言にメソッド本体（`...` 以外）がないこと。

検証失敗は `semantic_conflict` で fail-closed。

## 9. 将来拡張（対象外）

- デフォルト実装: Go で委譲メソッドの自動生成が必要になり、emitter 複雑度が跳ね上がるため v1 では見送り。
- trait bound（`@template("T: Comparable")`）: `@template` との連携。trait の基盤が安定してから着手。
- associated type: Rust の associated type 相当。需要が出てから検討。

## 10. 関連

- `docs/ja/spec/spec-type_id.md` — `type_id` / `trait_id` の定義
- `docs/ja/spec/spec-east.md` — EAST ノード仕様
- `docs/ja/spec/spec-emitter-guide.md` — emitter の写像規約
