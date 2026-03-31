<a href="../../en/spec/spec-adt.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# ADT (Algebraic Data Type) 仕様

この文書は、Pytra における union type の各言語への変換方針を定義する。

## 1. 背景

Python の union type (`int | str`, `str | None` 等) を静的型付け言語に変換するとき、これまでは全言語で C++ の `object` 実装（`{type_id, rc<RcObject>}`）に退化させていた。これにより:

- boxing / unboxing ノードが大量に生成される
- `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT` 等の補助機構が必要になる
- emitter が `object` 境界で崩れやすくなる

しかし、大半の言語は union / enum / variant / sealed class を持っており、`object` に退化させる必要がない。

## 2. 方針

**union type は言語ごとに最適な表現を使う。全言語を `object` に統一しない。**

## 3. 言語別の変換表

### 3.1 tagged union / enum をネイティブに持つ言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| Rust | `enum` | `if let Enum::Variant(x) = v` / `match` |
| Swift | `enum` with associated values | `if case let .variant(x) = v` |
| Kotlin | `sealed class` | `when (x) { is Type -> ... }` |
| Scala | `sealed trait` + `case class` | `match { case x: Type => ... }` |
| Nim | object variants | `case x.kind` |
| Zig | `union(enum)` | `switch (v)` |

これらの言語では `int | str` を直接 enum / variant に変換する。`object` への退化は不要。

例（Rust）:
```rust
enum IntOrStr {
    Int(i64),
    Str(String),
}

fn process(x: IntOrStr) {
    match x {
        IntOrStr::Int(n) => println!("{}", n),
        IntOrStr::Str(s) => println!("{}", s),
    }
}
```

### 3.2 variant 型を持つ言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| C++ | `std::variant<T1, T2, ...>` (非再帰)、`struct { variant<...> }` (再帰) | `std::holds_alternative<T>(v)` / `std::visit` |

C++ では非再帰と再帰で表現が異なる:

- **非再帰** (`int | str`, `str | None`): `using` による型エイリアスで `std::variant` を直接使う
- **再帰** (`JsonVal` のように自身を含む型): `struct` で包む。`using` は定義時点で右辺の型が完全でなければならず前方参照できないが、`struct` は宣言した時点で型名が存在し、メンバ定義は閉じ括弧までに確定すればよい。再帰 variant メンバは `shared_ptr` で包むことで RC 管理と前方参照を両立する

### C++ variant の RC 管理ルール

variant の各構成要素を `T` で持つか `std::shared_ptr<T>` で持つかは、Python で代入したとき共有されるか（mutable reference semantics）で決まる:

| union の構成要素 | variant に入れる型 | 理由 |
|---|---|---|
| POD (`int`, `float`, `bool`) | `int64_t`, `double`, `bool` | 値型。コピーで OK |
| `str` | `std::string` | immutable。コピーで OK |
| `None` | `std::monostate` | 値型 |
| value class (`class_storage_hint: "value"`) | `T` | 値型。コピーで OK |
| ref class (`class_storage_hint: "ref"`) | `std::shared_ptr<T>` | Python で共有される。RC 必須 |
| `list[T]`, `dict[K,V]`, `set[T]` | `std::shared_ptr<container<...>>` | Python ではミュータブルで共有される |
| 再帰参照 | `std::shared_ptr<T>` | 前方参照 + RC |

判定に使う EAST3 の情報:
- `class_storage_hint`: `"ref"` なら `shared_ptr`、`"value"` ならそのまま
- コンテナ型 (`list`, `dict`, `set`): 常に `shared_ptr`（Python のミュータブルコンテナは参照セマンティクス）
- POD / `str` / `None`: そのまま

例:
```cpp
// int | MyClass (MyClass は ref class)
using IntOrMyClass = std::variant<int64_t, std::shared_ptr<MyClass>>;

// str | list[int]
using StrOrList = std::variant<std::string, std::shared_ptr<std::vector<int64_t>>>;

// int | str | None (全て値型)
using IntOrStrOrNone = std::variant<int64_t, std::string, std::monostate>;
```

例（C++、非再帰）:
```cpp
using IntOrStr = std::variant<int64_t, std::string>;

void process(IntOrStr x) {
    if (std::holds_alternative<int64_t>(x)) {
        std::cout << std::get<int64_t>(x) << std::endl;
    } else {
        std::cout << std::get<std::string>(x) << std::endl;
    }
}
```

例（C++、再帰 — JsonVal）:
```cpp
struct JsonVal {
    struct Null {};
    std::variant<
        int64_t,
        double,
        bool,
        std::string,
        Null,
        std::shared_ptr<std::vector<JsonVal>>,
        std::shared_ptr<std::map<std::string, JsonVal>>
    > value;
};
```

### 3.3 sealed class / abstract record を持つ言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| C# | abstract record / sealed class | `x is Type t` / `switch (x)` |
| Java | sealed class (Java 17+) | `x instanceof Type t` (Java 16+) |
| Dart | sealed class (Dart 3+) | `switch (x) { case Type() => ... }` |

### 3.4 union type をネイティブに持つ言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| TypeScript | `T1 \| T2` そのまま | `typeof x === "..."` / discriminated union |
| JavaScript | 型注釈なし（元々動的） | `typeof x` |

TS は Python の union をそのまま出力できる。追加の構造体は不要。

### 3.5 動的型付け言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| Ruby | そのまま（全変数 object） | `x.is_a?(Type)` |
| Lua | そのまま | `type(x)` |
| PHP | union type hint (PHP 8+) | `$x instanceof Type` |
| PowerShell | そのまま | `-is [Type]` |
| Julia | `Union{T1, T2}` | `isa(x, Type)` |

動的型付け言語は元々全変数が `object` 相当なので、union の変換で特別な処理は不要。

### 3.6 `any` + GC を持つ言語

| 言語 | 変換先 | isinstance 相当 |
|---|---|---|
| Go | `any` (= `interface{}`) | `switch v := x.(type)` |

Go は tagged union / enum を持たないが、`any` + GC が Python の `object` セマンティクスにそのまま一致する。メソッド呼び出しは type assertion で具体型に落としてから行う。EAST3 の isinstance narrowing + Unbox がこのパターンを表現している。

### 3.7 ADT も GC もない言語のフォールバック（予備）

> 現時点の全ターゲット言語は tagged union / enum / variant / sealed class / `any` のいずれかを持っており、このフォールバックの該当言語はない。将来 ADT を持たない静的型付け言語が追加された場合の予備として残す。

tagged union を持たず、GC もない静的型付け言語では、struct + tag で表現する:

```
struct IntOrStr {
    tag: enum { Int, Str },
    int_val: i64,
    str_val: str,
}
```

全フィールドを持つためメモリは無駄になるが、ADT をサポートしない言語側の制約であり許容する。isinstance は tag フィールドを比較するだけ。

## 4. 再帰型の扱い

`JsonVal` のように自身を含む再帰的な ADT は、一部の言語でポインタが必要:

| 言語 | 再帰型の扱い |
|---|---|
| Rust | `enum JsonVal { Arr(Vec<Box<JsonVal>>), ... }` — Box でポインタ化 |
| C++ | `struct JsonVal { std::variant<..., rc<std::vector<JsonVal>>> value; }` — struct で包み、再帰 variant を rc でポインタ化。`using` は前方参照不可だが `struct` なら宣言時点で型名が存在するため可能 |
| Zig | `*JsonVal` でポインタ化 + 自前 RC or arena allocator |
| Go | `any` で問題なし（GC 管理） |
| Swift | `indirect enum` で明示 |
| TS | 直接書ける（`type JsonVal = number \| JsonVal[]`） |
| C#/Java/Kotlin/Scala/Dart | 参照型なので自然に再帰可能 |

非再帰 union (`int | str`, `str | None`) はどの言語でも問題なし。

**再帰型であっても `object` への退化は禁止。** 各言語のポインタ / RC / GC 機構を使って ADT として表現する。

## 5. EAST3 との関係

### 5.1 EAST3 の union 表現

EAST3 は union を以下のノードで保持する（spec-east.md §6.3-6.4）:

- `OptionalType`: `T | None` の正規形
- `UnionType(union_mode=general)`: 一般 union (`int | str`)
- `UnionType(union_mode=dynamic)`: `Any/object` を含む dynamic union
- `NominalAdtType`: `JsonVal` 等の closed nominal ADT

### 5.2 emitter の責務

- emitter は `UnionType` を見て §3 の変換表に従い言語固有の表現を生成する
- `UnionType` を `object` に退化させるのは **`union_mode=dynamic` の場合のみ**
- `union_mode=general` の union を `object` に退化させてはならない
- `OptionalType` は union ではなく Optional（`T?`, `Option<T>`, `T | null` 等）として生成する

### 5.3 isinstance narrowing

EAST3 の isinstance narrowing（Unbox ノード）は、全言語の ADT パターンマッチに対応する:

| EAST3 | Rust | C++ | Go | TS |
|---|---|---|---|---|
| isinstance(x, int) → Unbox | `if let Enum::Int(n) = x` | `std::holds_alternative<int64_t>(x)` | `n, ok := x.(int64)` | `typeof x === "number"` |

emitter は Unbox ノードを見て言語固有のパターンマッチ構文を生成するだけ。

## 6. `object` への退化は全面禁止

union type を `object` に退化させることを **全面禁止** する。

- `Any` 型注釈は Pytra で禁止されている。`object` が生成される入口がない
- 再帰 ADT も §4 のとおり、各言語のポインタ / RC / GC 機構で ADT として表現できる
- 動的型付け言語は元々全変数が動的型なので、ADT の変換は不要（言語のネイティブ表現をそのまま使う）

これにより:
- lowering が union を `object` に退化させる必要がなくなる
- boxing / unboxing ノードは消える
- `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT` 等の `object` 境界の補助機構は不要になる
- emitter は `object` パスを持つ必要がない

## 7. 関連

- [spec-east.md](./spec-east.md) §6.3-6.5: TypeExpr / union 3分類 / NominalAdtType
- [spec-tagged-union.md](./spec-tagged-union.md): `type X = A | B` の宣言
- [spec-boxing.md](./spec-boxing.md): Any/object 境界の型変換
- [plan-union-to-nominal-adt.md](../plans/plan-union-to-nominal-adt.md): 移行計画
