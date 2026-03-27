<a href="../../en/spec/spec-tagged-union.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# tagged union 仕様

この文書は、Pytra における `type X = A | B | ...` 宣言（PEP 695 型エイリアスによる union 型定義）の意味・コード生成規則・型操作規則を定義する。

## 1. 目的

- Python の `type X = A | B | ...` 宣言から、各ターゲット言語のネイティブな tagged union を生成する。
- 再帰型（`type JsonVal = ... | list[JsonVal] | dict[str, JsonVal]`）を自然に表現可能にする。
- `isinstance` / `is None` / `cast` を統一的な `type_id` ベースで実現する。

## 2. 宣言

モジュールレベルの `type` 文（PEP 695）で宣言する。

```python
type ArgValue = str | bool | None
type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
```

- 2 型以上の union（`None` を除く non-none メンバが 2 つ以上）は tagged union として扱う。
- 1 型 + `None` は `Optional[T]` として扱い、tagged union にはならない。
- Generic type alias（`type Stack[T] = list[T]`）は対象外。

## 3. C++ コード生成

tagged union は `struct` + `uint32 tag` として emit される。tag 値は `PYTRA_TID_*` 定数を使用する。

```cpp
struct ArgValue {
    uint32 tag;
    str str_val;
    bool bool_val;

    ArgValue() : tag(PYTRA_TID_NONE) {}
    ArgValue(const str& v) : tag(PYTRA_TID_STR), str_val(v) {}
    ArgValue(const bool& v) : tag(PYTRA_TID_BOOL), bool_val(v) {}
    ArgValue(::std::monostate) : tag(PYTRA_TID_NONE) {}
};
```

### 3.1 tag 値

tag 値は `spec-type_id.md` で定義された `PYTRA_TID_*` 定数を直接使用する。

| Python 型 | tag 値 |
|-----------|--------|
| `None` | `PYTRA_TID_NONE` |
| `bool` | `PYTRA_TID_BOOL` |
| `int` | `PYTRA_TID_INT` |
| `float` | `PYTRA_TID_FLOAT` |
| `str` | `PYTRA_TID_STR` |
| `list[T]` | `PYTRA_TID_LIST` |
| `dict[K,V]` | `PYTRA_TID_DICT` |
| `set[T]` | `PYTRA_TID_SET` |
| ユーザークラス | `ClassName::PYTRA_TYPE_ID` |

### 3.2 再帰型

自身を含む union メンバ（`list[JsonVal]` 等）は `rc<list<JsonVal>>` のように参照カウントポインタで包む。

## 4. isinstance 判定

tagged union 変数への `isinstance` は tag 比較に変換される。

```python
isinstance(v, int)   # v: JsonVal
```
→ C++:
```cpp
(v).tag == PYTRA_TID_INT
```

クラス型の場合は `py_tid_is_subtype` によるレンジ判定を使用し、継承関係を尊重する。

## 5. 型ナローイング（cast）

tagged union 変数から特定の型の値を取り出すには `typing.cast` を使用する。

```python
from pytra.typing import cast

if isinstance(v, int):
    x = cast(int, v)      # v の int 値を取り出す
    print(x + 1)
```
→ C++:
```cpp
if ((v).tag == PYTRA_TID_INT) {
    int64 x = v.int64_val;
    py_print(x + 1);
}
```

### 5.1 規則

- `cast(T, v)` は tagged union 変数 `v` から型 `T` に対応するフィールドへのアクセスに変換される。
- Python 実行時は `typing.cast` は no-op（値をそのまま返す）なので、Python でもそのまま動作する。
- `isinstance` ガードなしで `cast` を呼ぶことは可能だが、tag が一致しない場合の動作は未定義。
- **isinstance ガードによる暗黙のナローイングは行わない。** 型を確定させるには明示的に `cast()` を使用する。

### 5.2 フィールド名規則

tagged union の各メンバのフィールド名は `型名.lower() + "_val"` で生成される。

| Python 型 | フィールド名 |
|-----------|-------------|
| `bool` | `bool_val` |
| `int` | `int64_val` |
| `float` | `float64_val` |
| `str` | `str_val` |
| `list[T]` | `list_t_val` |
| `dict[K,V]` | `dict_k_v_val` |

## 6. is None 判定

```python
if v is None:     # → v.tag == PYTRA_TID_NONE
if v is not None: # → v.tag != PYTRA_TID_NONE
```

## 7. None 既定値

tagged union 型の引数のデフォルト値 `None` は、デフォルトコンストラクタ（`tag = PYTRA_TID_NONE`）に変換される。

## 8. 他言語での emit 戦略

| 言語 | 機構 |
|------|------|
| Rust | `enum` |
| Swift | `indirect enum` |
| Kotlin/Java | sealed class |
| Scala | sealed trait + case class |
| TypeScript | discriminated union |
| Go | struct + tag |

各バックエンドでの対応は後続タスクとする。
