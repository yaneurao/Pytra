# built-in 関数仕様（ドラフト）

最終更新: 2026-03-24
ステータス: ドラフト（検討中）

## 1. 目的

Python の built-in 関数（`len`, `str`, `print` 等）の型情報を、ハードコードテーブルではなく `.py` ファイルの宣言として提供する。resolve 段がこの宣言の EAST1 を読んで型解決する。

## 2. 型の二分類: POD と Obj

Pytra の全ての値は POD（プリミティブ値型）か Obj（参照型）のいずれかに分類される。

- **POD**: `None`, `bool`, `int8`〜`int64`, `uint8`〜`uint64`, `float32`, `float64`, `str`
  - immutable。メソッドを持たない（`str` は例外で一部メソッドを持つ）。
  - コピーは値のコピー。
- **Obj**: `list[T]`, `dict[K,V]`, `set[T]`, `tuple[T,...]`, `Path`, ユーザー定義クラス
  - dunder メソッド（`__len__`, `__str__` 等）を持ちうる。
  - 参照セマンティクス。

`Obj` は言語非依存の概念であり、Python 固有ではない。`pytra/types.py` に `POD` と `Obj` を定義する。

resolve は built-in 関数の引数型が `Obj` の場合、実引数の具象型に該当の dunder メソッドがあるかを静的にチェックし、なければ `semantic_conflict` で拒否する。

## 3. 設計方針: dunder メソッド委譲

Python の built-in 関数の多くは、オブジェクトの dunder メソッドへの委譲として定義される。

```python
len(x)     →  x.__len__()
str(x)     →  x.__str__()
bool(x)    →  x.__bool__()
int(x)     →  x.__int__()
float(x)   →  x.__float__()
repr(x)    →  x.__repr__()
iter(x)    →  x.__iter__()
next(x)    →  x.__next__()
```

この設計により:
- built-in 関数の型は dunder メソッドの戻り値型から導出できる
- 新しい型（ユーザー定義クラス）でも dunder を実装すれば built-in が使える
- emitter は dunder を各言語の慣用表現に写像するだけ

## 3. built-in 関数の宣言

### 3.1 dunder 委譲型（オブジェクトの dunder を呼ぶ）

```python
def len(x: Obj) -> int:
    return x.__len__()

def str(x: Obj) -> str:
    return x.__str__()

def bool(x: Obj) -> bool:
    return x.__bool__()

def int(x: Obj) -> int:
    return x.__int__()

def float(x: Obj) -> float:
    return x.__float__()

def repr(x: Obj) -> str:
    return x.__repr__()
```

### 3.2 スタンドアロン型（dunder に委譲しない）

各言語の runtime が実装する関数。`@extern` で宣言し、body には Python fallback を書く（`pass` でもよい）。resolve はシグネチャのみ参照し、body は無視する。トランスパイル時は emitter が各言語の runtime に写像する。

```python
@extern
def print(*args: Obj) -> None:
    pass  # runtime 実装
# resolve が *args: Obj → args: list[Obj] に変換。
# 呼び出し側 print(a, b, c) → print([a, b, c]) に変換。
# list[Obj] に POD を入れる場合の boxing は compile 段で命令化。

@extern
def isinstance(x: Obj, t: type) -> bool:
    pass  # runtime 実装

@extern
def issubclass(cls: type, parent: type) -> bool:
    pass  # runtime 実装

@extern
def round(x: float, ndigits: int = 0) -> int:
    pass  # runtime 実装

@extern
def abs(x: int) -> int:
    pass  # runtime 実装

@extern
def ord(c: str) -> int:
    pass  # runtime 実装

@extern
def chr(i: int) -> str:
    pass  # runtime 実装
```

### 3.3 ジェネリック型（`@template` を使用）

既存の `@template` デコレータで型パラメータを宣言する。resolve は callsite の具象型から `T` を解決する（例: `min(a, b)` で `a: int64, b: int64` なら `T = int64`、戻り値 `int64`）。

linker が implicit instantiation を行い、EAST3 には具象化済みの関数が含まれる。emitter はジェネリクスがある言語では `min[T]` で出し、ない言語では `min_int64` 等の具象関数として出す。

```python
@template("T")
@extern
def min(a: T, b: T) -> T:
    pass

@template("T")
@extern
def max(a: T, b: T) -> T:
    pass

@template("T")
@extern
def sorted(x: list[T]) -> list[T]:
    pass

@template("T")
@extern
def reversed(x: list[T]) -> list[T]:
    pass

@template("T")
@extern
def enumerate(x: list[T], start: int = 0) -> list[tuple[int, T]]:
    pass

@template("T", "U")
@extern
def zip(a: list[T], b: list[U]) -> list[tuple[T, U]]:
    pass
```

### 3.4 range（特殊: resolve で ForRange に変換）

```python
@extern
def range(stop: int) -> list[int]:
    pass

@extern
def range(start: int, stop: int) -> list[int]:
    pass

@extern
def range(start: int, stop: int, step: int) -> list[int]:
    pass
```

resolve は引数の数から `start/stop/step` を正規化し、`for x in range(n)` を `ForRange` ノードに、式位置の `range(...)` を `RangeExpr` に変換する。emitter には関数呼び出しとして届かないため、オーバーロード非対応の言語でも問題ない。body は実行されないので `pass` でよい。

## 4. コンテナ型の dunder メソッド宣言

クラスレベルの `@template` で型パラメータを宣言する。resolve は変数の具象型（`list[int64]` 等）から `T` を束縛し、メソッドの戻り値型を解決する。

引数の型は exact match を要求する。`list[int16].extend(list[int8])` のような暗黙の型変換は行わず、`semantic_conflict` で拒否する。

### 4.1 list

```python
@template("T")
class list:
    def __len__(self) -> int: pass
    def __str__(self) -> str: pass
    def __bool__(self) -> bool: pass
    def __iter__(self) -> Iterator[T]: pass
    def append(self, x: T) -> None: pass
    def extend(self, x: list[T]) -> None: pass
    def pop(self, index: int = -1) -> T: pass
    def insert(self, index: int, x: T) -> None: pass
    def remove(self, x: T) -> None: pass
    def clear(self) -> None: pass
    def reverse(self) -> None: pass
    def sort(self) -> None: pass
    def copy(self) -> list[T]: pass
    def index(self, x: T) -> int: pass
    def count(self, x: T) -> int: pass
```

### 4.2 str

```python
class str:
    def __len__(self) -> int: pass
    def __str__(self) -> str: pass
    def __bool__(self) -> bool: pass
    def __int__(self) -> int: pass
    def __float__(self) -> float: pass
    def upper(self) -> str: pass
    def lower(self) -> str: pass
    def strip(self) -> str: pass
    def split(self, sep: str = " ") -> list[str]: pass
    def join(self, parts: list[str]) -> str: pass
    def startswith(self, prefix: str) -> bool: pass
    def endswith(self, suffix: str) -> bool: pass
    def find(self, sub: str) -> int: pass
    def replace(self, old: str, new: str) -> str: pass
    def isdigit(self) -> bool: pass
    def isalpha(self) -> bool: pass
```

### 4.3 dict

```python
@template("K", "V")
class dict:
    def __len__(self) -> int: pass
    def __str__(self) -> str: pass
    def __bool__(self) -> bool: pass
    def keys(self) -> list[K]: pass
    def values(self) -> list[V]: pass
    def items(self) -> list[tuple[K, V]]: pass
    def get(self, key: K, default: V = None) -> V: pass
    def pop(self, key: K) -> V: pass
    def setdefault(self, key: K, default: V = None) -> V: pass
    def clear(self) -> None: pass
    def update(self, other: dict[K, V]) -> None: pass
```

### 4.4 set

```python
@template("T")
class set:
    def __len__(self) -> int: pass
    def __str__(self) -> str: pass
    def __bool__(self) -> bool: pass
    def add(self, x: T) -> None: pass
    def discard(self, x: T) -> None: pass
    def remove(self, x: T) -> None: pass
    def clear(self) -> None: pass
```

## 5. resolve での型解決フロー

1. `built_in.py` を parse して EAST1 を得る
2. EAST1 の `FunctionDef` / `ClassDef` からシグネチャを抽出
3. ユーザーコードの `len(x)` を見たとき:
   - `len` の宣言から戻り値型 `int` を取得
   - 引数 `x` の型が `list[int64]` なら、`x.__len__()` の戻り値型 `int` を確認
4. `x.append(v)` を見たとき:
   - `x` の型 `list[int64]` から `list` の `append` メソッドを検索
   - シグネチャから戻り値型 `None` を取得
5. resolve が dunder 委譲を展開するかどうかは実装次第
   - 型解決の観点では、`len(x) -> int` と知っていれば十分
   - dunder 展開は emitter の責務としてもよい

## 6. emitter での dunder 写像

| Python | C++ | Go | Rust | Java |
|---|---|---|---|---|
| `x.__len__()` | `x.size()` | `len(x)` | `x.len()` | `x.size()` |
| `x.__str__()` | `py_to_string(x)` | `fmt.Sprint(x)` | `x.to_string()` | `x.toString()` |
| `x.__bool__()` | `py_to_bool(x)` | `len(x) > 0` | `!x.is_empty()` | `!x.isEmpty()` |
| `x.__int__()` | `static_cast<int64_t>(x)` | `int64(x)` | `x as i64` | `(long)x` |

## 7. ファイル配置

```
src/pytra/built_in/
  builtins.py          ← built-in 関数の宣言（len, str, print 等）
  containers.py        ← コンテナ型の dunder + メソッド宣言（list, dict, str, set）
  io_ops.py            ← 既存（py_print 等のランタイムヘルパー）
  sequence.py          ← 既存（py_range 等のランタイムヘルパー）
  ...
```

`builtins.py` と `containers.py` は宣言のみ（関数本体は `pass` または Python fallback）。resolve はシグネチャのみ参照する。ランタイムヘルパー（`py_print` 等）は既存ファイルに維持。

## 8. varargs の変換ルール

`*args: T` は resolve が以下のように変換する:

- 宣言側: `*args: T` → `args: list[T]`
- 呼び出し側: `f(a, b, c)` → `f([a, b, c])`
- `list[Obj]` に POD 値を入れる場合の boxing 命令化は compile 段（EAST2→EAST3）の責務

例:

```
# ソース
print(1, "hello", 3.14)

# resolve 後 (EAST2)
print([1, "hello", 3.14])    # 型: list[Obj]

# compile 後 (EAST3)
print([ObjBox(1), "hello", ObjBox(3.14)])  # POD を boxing
```

## 9. 未決事項

- ~~`object` を引数型にしてよいか~~ → `Obj` 型で解決。`object` は使わない。
- ~~ジェネリック型パラメータ `T` の表現~~ → `@template` をクラスにも適用。
- ~~`print` の可変長引数 `*args` の扱い~~ → `*args: T` を `args: list[T]` に resolve が変換。
- ~~`range` のオーバーロード~~ → resolve が `start/stop/step` に正規化し `ForRange` / `RangeExpr` に変換。emitter には届かない。
- dunder 展開のタイミング（resolve で展開するか、emitter に任せるか）
- `min`/`max` の引数が 2 個以上の場合（可変長か、2 引数固定か）
- `int(x, base=16)` のような base 引数付き変換の扱い
- コンテナ型の宣言が `src/pytra/built_in/` にあるべきか、`src/pytra/std/` にあるべきか
