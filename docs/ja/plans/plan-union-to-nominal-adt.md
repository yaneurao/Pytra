# 計画: union type を nominal ADT ベースに移行する

## 背景

現在の EAST3 lowering は `int | str` のような union type を `object` に退化させ、boxing / unboxing / type_id dispatch で処理している。これは C++ の `object` 実装（`{type_id, rc<RcObject>}`）を全言語の規範としたためだが、以下の問題を引き起こしている:

- box/unbox ノードの大量生成
- `yields_dynamic` / `Unbox` / `OBJ_ITER_INIT` 等の複雑な補助機構
- selfhost で `JsonVal`（= `Any` = `object`）が出るたびに emitter が崩れる
- `dict.items()` の戻り値型が `list[tuple[K,V]]` にハックされる等のしわ寄せ

## 方針

**union type を `object` に退化させず、言語ごとに最適な表現を使う。**

### 言語別の union 表現

| 言語群 | union の表現 | 備考 |
|---|---|---|
| **Rust, Swift, Kotlin, Scala, Nim** | enum / tagged union | ネイティブサポート |
| **Zig** | tagged union | 再帰型でポインタ必須。C++ と同じく再帰 ADT は RC 管理が課題 |
| **C++** | `std::variant`（非再帰のみ） or 継承 | 再帰型は `std::variant` + ポインタだと RC 管理が壊れる。再帰 ADT は継承ベース or 既存 `object` 実装を維持 |
| **TS/JS** | union type そのまま | 言語が union を直接サポート |
| **C#, Java, Dart** | sealed class / abstract record | パターンマッチで網羅性チェック可能 |
| **Go** | interface + struct | boilerplate は多いが表現可能 |
| **Ruby, Lua, PHP, PowerShell, Julia** | 動的型（そのまま） | 元々全変数が object 相当なので問題なし |

### EAST3 での扱い

- EAST3 は `UnionType` / `NominalAdtType` をそのまま保持する（今も保持している）
- lowering が `object` に退化させるのを**やめる**
- emitter は `UnionType` を見て言語固有の表現を生成する
- boxing / unboxing は `object` 境界でのみ発生（`Any` 型注釈がある場合のみ）

### anonymous union → nominal ADT への変換

`int | str` のような anonymous union は、EAST3 optimizer または linker で nominal ADT に変換できる:

```python
# ユーザーが書くコード
x: int | str = ...

# 内部的に生成される ADT
# (ユーザーには見えない)
enum __Union_int_str {
    Int(int64),
    Str(str),
}
```

ただし、これは全言語で必要ではない（TS は anonymous union をそのまま使える）。言語 profile に `union_strategy: "nominal_adt" | "native_union" | "object_fallback"` を持たせ、emitter が参照する。

### 再帰型の制約

`JsonVal` のように自身を含む再帰的な ADT は、C++ と Zig でポインタが必要になる:

- C++: `std::variant<..., std::unique_ptr<JsonVal>>` にすると RC 管理が壊れる（`unique_ptr` は共有不可、`shared_ptr` はアクセスに間接参照が必要で emitter が煩雑に）
- Zig: 同じくポインタ必須で RC と相性が悪い
- Rust: `Box<JsonVal>` で問題なし（所有権が明確）

再帰 ADT に対する C++/Zig の選択肢:

1. **継承ベース**: `class JsonVal { virtual ~JsonVal(); }` + 派生クラス。vtable で dispatch。RC は `shared_ptr<JsonVal>` で統一
2. **既存 `object` 実装を維持**: 再帰 ADT だけ `object` ベースで処理（`type_id` + `rc<RcObject>`）
3. **Rust 方式を模倣**: `std::variant<..., std::unique_ptr<JsonVal>>` + arena allocator で寿命管理

現実的には、非再帰 union (`int | str`, `str | None`) は `std::variant` を使い、再帰 ADT (`JsonVal`) は継承ベースか既存 `object` を維持する二段構えが妥当。前回の検討で `std::variant` が全面採用できなかったのはこの再帰型の RC 問題が理由。

## `dict.items()` 等の iterable 問題との関係

`dict.items()` が `list[tuple[K,V]]` にハックされている問題は、この方針と直交する:

- union / ADT の改善: `int | str` を `object` に退化させない → box/unbox が減る
- iterable の改善: `dict.items()` を正しい iterable として扱う → `list` ハックが消える

両方やる必要があるが、独立して進められる。

## 段階的移行

### Phase 1: EAST3 の union 保持を確認

- EAST3 が `UnionType` を正しく保持していることは確認済み
- `dict[str, str | int | None]` は `UnionType([str, int64, None])` になる（確認済み）
- lowering が `object` に退化させる箇所を特定（lower.py の 597行目、2042-2075行目）

### Phase 2: lowering の `object` 退化を段階的に除去

- まず `JsonVal` nominal ADT を `object` と同一視するのをやめる（lower.py:910）
- 次に boxing の `resolved_type="object"` を union 型のまま保持するよう変更
- iter boundary の `object` は iterable 改善と合わせて対処

### Phase 3: emitter の union 対応

- C++ emitter: `UnionType` → `std::variant<T1, T2, ...>` を生成
- Rust emitter: `UnionType` → `enum` を生成
- TS emitter: `UnionType` → `T1 | T2` をそのまま出力
- Go emitter: `UnionType` → interface + type switch
- 動的型言語: 変更なし

### Phase 4: `@template` class 対応 + Iterable

- class template を実装し、`dict_items<K,V>` 等の generic iterable を定義可能にする
- `Iterable[T]` trait を定義し、`for` の iter プロトコルを統一する
- これは union/ADT とは独立だが、合わせて進めることで `object` の残存箇所がさらに減る

## 完了条件

- 非再帰 union は `std::variant` / enum 等の nominal ADT で表現される（`object` に退化しない）
- 再帰 ADT は C++/Zig で継承ベース or 既存 `object` を使用（RC 管理の制約）
- `object` に退化するのは `Any` 型注釈がある場合と再帰 ADT の C++/Zig のみ
- union type を使った fixture が全言語で compile + run parity PASS
- selfhost コードの `JsonVal` が `object` ではなく nominal ADT として処理される
- box/unbox ノードが union → object 退化に起因するケースでは生成されない
