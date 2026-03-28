<a href="../../en/plans/p6-extern-method-redesign.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6-EXTERN-METHOD-REDESIGN: @extern_method / @abi の再設計

最終更新: 2026-03-28
ステータス: 案

## 背景

現在 `containers.py` 等の built_in 宣言は `@extern_method` + `@abi` の2デコレータを使うが:

- `@extern_method` の引数が冗長（module, symbol, tag の3つ）
- `@abi` は未使用（実装もテストもない）だが、escape 解析に必要な arg_usage 情報を持つ予定だった
- `@abi` の名前が「ABI 境界」を想起させ、実際の用途（readonly/mutable 宣言）と乖離

## 現状

```python
@extern_method(module="pytra.core.list", symbol="list.extend", tag="stdlib.method.extend")
@abi(args={"x": "value"})
def extend(self, x: list[T]) -> None: ...
```

問題:
- 1行が長い
- `@abi` は未実装で、使っているコードがない
- `module` と `symbol` と `tag` に重複情報がある（`list.extend` が2回出現）

## 提案

### 案A: `@method` に統合、tag 自動導出

```python
@method("pytra.core.list.extend")
def extend(self, x: list[T]) -> None: ...
```

- module + symbol を1引数にまとめる（`pytra.core.list.extend` → module は `pytra.core.list`、symbol は `extend`、最後の `.` で分割）
- tag は `module + "." + symbol` から自動導出（`stdlib.method.extend` 相当）。明示が必要な場合だけ `tag=` で上書き
- arg_usage が必要な場合:

```python
@method("pytra.core.list.extend", x="readonly")
def extend(self, x: list[T]) -> None: ...
```

### 案B: `@method` + `@usage` の2デコレータ

```python
@method("pytra.core.list.extend")
@usage(x="readonly")
def extend(self, x: list[T]) -> None: ...
```

- `@abi` を `@usage` にリネーム。意味が明確
- arg_usage がないメソッドは `@method` だけで済む

### 案C: `@method` に kwargs で arg_usage 統合

```python
@method("pytra.core.list.extend", args={"x": "readonly"})
def extend(self, x: list[T]) -> None: ...
```

- 1デコレータで完結
- ただし `args={"x": "readonly"}` が冗長

### 案D: `@namespace` + `@method` 最小記述（class名・メソッド名から自動導出）

```python
# containers.py 冒頭
@namespace("pytra.core")

class list(Generic[T]):

    @method
    def append(self, x: T) -> None: ...

    @method(x="readonly")
    def extend(self, x: list[T]) -> None: ...

    @method
    def pop(self, index: int = -1) -> T: ...

    @method(key="readonly")
    def sort(self, key: str = "") -> None: ...

class dict(Generic[K, V]):

    @method
    def get(self, key: K) -> V: ...

    @method
    def items(self) -> list[tuple[K, V]]: ...
```

自動導出ルール:
- module: `@namespace` + class名 → `pytra.core.list`
- symbol: class名 + メソッド名 → `list.extend`
- tag: `stdlib.method.` + メソッド名 → `stdlib.method.extend`（自動導出）
- arg_usage: `@method` の kwargs で指定。指定なしはデフォルト mutable

runtime 側の関数名変換（`list.extend` → `py_list_extend_mut` 等）は mapping.json の責務。`@method` には書かない。

## 比較

現状と各案の `containers.py` の書き味:

### append（self=mutable, arg_usage なし）

| 方式 | 記述 |
|---|---|
| 現状 | `@extern_method(module="pytra.core.list", symbol="list.append", tag="stdlib.method.append")` |
| 案A | `@method("pytra.core.list.append")` |
| 案B | `@method("pytra.core.list.append")` |
| 案C | `@method("pytra.core.list.append")` |
| **案D** | **`@method`** |

### extend（x=readonly）

| 方式 | 記述 |
|---|---|
| 現状 | `@extern_method(...)` + `@abi(args={"x": "value"})` |
| 案A | `@method("pytra.core.list.extend", x="readonly")` |
| 案B | `@method("pytra.core.list.extend")` + `@usage(x="readonly")` |
| 案C | `@method("pytra.core.list.extend", args={"x": "readonly"})` |
| **案D** | **`@method(x="readonly")`** |

### sort（self=mutable, key=readonly）

| 方式 | 記述 |
|---|---|
| 現状 | `@extern_method(...)` + `@abi(args={"key": "value"})` |
| 案A | `@method("pytra.core.list.sort", key="readonly")` |
| 案B | `@method("pytra.core.list.sort")` + `@usage(key="readonly")` |
| 案C | `@method("pytra.core.list.sort", args={"key": "readonly"})` |
| **案D** | **`@method(key="readonly")`** |

## 推奨

**案D** が最も簡潔。

- arg_usage がないメソッド（大半）は `@method` の1語だけ
- arg_usage があるメソッドは `@method(x="readonly")` だけ
- module / symbol / tag はクラス名・メソッド名・`@namespace` から全自動導出
- パス指定が一切不要
- runtime 関数名の変換は mapping.json の責務（`@method` には書かない）
- `@abi` は廃止（未実装・未使用なので影響ゼロ）
- `@extern_method` は `@method` + `@namespace` に置き換え

注意:
- `@namespace` はファイル冒頭に1回だけ書く
- parser が `@namespace` + class名 + メソッド名から module / symbol / tag を自動導出する実装が必要
- `self` はデフォルト mutable。明示不要。
- arg_usage を指定しない引数はデフォルト「escape する（mutable）」として扱う（安全側）

## @abi の廃止

- `@abi` は未実装・未使用なので、廃止しても影響ゼロ
- spec-east.md の `meta.runtime_abi_v1` は `meta.arg_usage_v1` にリネーム
- チュートリアル・ガイドの `@abi` 言及を削除

## escape 解析との連携

- `@method` の arg_usage（`readonly` / デフォルト mutable）を EAST3 の `FunctionDef.meta.arg_usage_v1` に保持
- escape 解析は `arg_usage_v1` を見て「この引数は readonly なので、渡しても escape しない」と判断
- 非 extern 関数は resolve が本体を解析して `arg_usage` を自動算出（既存の仕組み）
- extern 関数だけ `@method` の宣言から取得

## 未決事項

- `@method` と `@extern` の関係整理（`@extern` は関数用、`@method` はメソッド用？ それとも統合？）
- `@extern` も同様に短縮できるか
- 既存の `containers.py` の書き換え量
