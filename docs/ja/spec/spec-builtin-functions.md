<a href="../../en/spec/spec-builtin-functions.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
def min(*args: T) -> T:
    pass
# resolve が *args: T → args: list[T] に変換。
# optimize が要素数 2 のケースを py_min2(a, b) に特殊化してもよい。

@template("T")
@extern
def max(*args: T) -> T:
    pass
# 同上。

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

1. `built_in.py` / `containers.py` を parse して EAST1 を得る
2. EAST1 の `FunctionDef` / `ClassDef` からシグネチャを抽出
3. ユーザーコードの `len(x)` を見たとき:
   - 引数 `x` の型がコンテナ型の宣言で `__len__` を持つか確認（型チェック）
   - 持っていなければ `semantic_conflict` で拒否
   - 戻り値型 `int` を解決
   - **ノードを `py_len(x)` に変換**（`len` は EAST2 に残さない）
4. 同様に `str(x)` → `py_str(x)`, `bool(x)` → `py_bool(x)` 等に変換
5. `x.append(v)` を見たとき:
   - `x` の型 `list[int64]` から `list` の `append` メソッドを検索
   - シグネチャから戻り値型 `None` を取得
   - メソッド呼び出しはそのまま残す（`py_` prefix にしない）
6. dunder メソッド（`__len__` 等）はノード変換には使わない。型チェック（「この型に `__len__` があるか」）にのみ使用する

### 5.1 built-in → py_ 変換テーブル

| Python built-in | EAST2 ノード | 戻り値型 |
|---|---|---|
| `len(x)` | `py_len(x)` | `int` |
| `str(x)` | `py_str(x)` | `str` |
| `bool(x)` | `py_bool(x)` | `bool` |
| `int(x)` | `py_int(x)` | `int` |
| `float(x)` | `py_float(x)` | `float` |
| `repr(x)` | `py_repr(x)` | `str` |
| `print(...)` | `py_print(...)` | `None` |
| `abs(x)` | `py_abs(x)` | 引数型 |
| `ord(c)` | `py_ord(c)` | `int` |
| `chr(i)` | `py_chr(i)` | `str` |
| `isinstance(x, t)` | `py_isinstance(x, t)` | `bool` |

`py_` prefix により:
- frontend の言語に依存しない一意な識別子になる
- 将来の Ruby/Kotlin 等の frontend からも同じ `py_len` に変換される
- emitter は `py_len` を各言語の runtime に写像するだけ

## 6. emitter での dunder 写像

| Python | C++ | Go | Rust | Java |
|---|---|---|---|---|
| `x.__len__()` | `x.size()` | `len(x)` | `x.len()` | `x.size()` |
| `x.__str__()` | `py_to_string(x)` | `fmt.Sprint(x)` | `x.to_string()` | `x.toString()` |
| `x.__bool__()` | `py_to_bool(x)` | `len(x) > 0` | `!x.is_empty()` | `!x.isEmpty()` |
| `x.__int__()` | `static_cast<int64_t>(x)` | `int64(x)` | `x as i64` | `(long)x` |

## 7. `pytra: builtin-declarations` ディレクティブ

ファイル先頭のコメントに `pytra: builtin-declarations` と記述すると、そのファイルは「宣言のみ（emit 対象外）」として扱われる。

```python
# pytra: builtin-declarations

@extern_fn(module="pytra.core.py_runtime", symbol="len", tag="core.len")
def len(x: Obj) -> int: ...
```

各言語のコメント記法で書くが、ディレクティブ文字列は共通:

| 言語 | 記法 |
|---|---|
| Python | `# pytra: builtin-declarations` |
| C++ | `// pytra: builtin-declarations` |
| Go | `// pytra: builtin-declarations` |
| Rust | `// pytra: builtin-declarations` |

処理の流れ:

1. **parse**: 先頭行のコメントから `pytra: builtin-declarations` を検出し、EAST1 の `meta.declaration_only: true` を付与
2. **resolve**: EAST1 の `FunctionDef` / `ClassDef` からシグネチャを抽出し、型解決に使用
3. **emit**: `meta.declaration_only == true` のモジュールをスキップ（コード生成しない）

ユーザーも同じ仕組みで独自の built-in を定義できる:

```python
# pytra: builtin-declarations

@extern_fn(module="my_game.physics", symbol="apply_gravity", tag="user.physics.gravity")
def apply_gravity(x: float, y: float, dt: float) -> float: ...
```

## 8. ファイル配置

```
src/pytra/built_in/
  builtins.py          ← built-in 関数の宣言（len, str, print 等）
  containers.py        ← コンテナ型の dunder + メソッド宣言（list, dict, str, set）
  io_ops.py            ← 既存（py_print 等のランタイムヘルパー）
  sequence.py          ← 既存（py_range 等のランタイムヘルパー）
  ...
```

`builtins.py` と `containers.py` は宣言のみ（関数本体は `pass` または Python fallback）。resolve はシグネチャのみ参照する。ランタイムヘルパー（`py_print` 等）は既存ファイルに維持。

## 9. varargs の変換ルール

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

## 10. v2 extern: `extern_fn` / `extern_var` / `extern_class`

v2 では `@extern` を用途別に 3 つに分離し、`module` / `symbol` / `tag` を必須引数とする。

### 10.1 `extern_fn` — 外部関数宣言

```python
@extern_fn(module="pytra.built_in.io_ops", symbol="py_print", tag="core.print")
def print(*args: Obj) -> None: ...

@extern_fn(module="pytra.std.math", symbol="sqrt", tag="stdlib.method.sqrt")
def sqrt(x: float) -> float: ...
```

### 10.2 `extern_var` — 外部変数宣言

```python
pi: float = extern_var(module="pytra.std.math", symbol="pi", tag="stdlib.symbol.pi")
argv: list[str] = extern_var(module="pytra.std.sys", symbol="argv", tag="stdlib.symbol.argv")
```

### 10.3 `extern_class` — 外部クラス宣言

```python
@extern_class(module="pytra.std.pathlib", symbol="Path", tag="stdlib.class.Path")
class Path:
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def write_text(self, text: str, encoding: str = "utf-8") -> int: ...
```

### 10.4 引数

| 引数 | 意味 | 必須 |
|---|---|---|
| `module` | 実装がある runtime モジュール（言語非依存） | 必須 |
| `symbol` | runtime モジュール内での名前 | 必須 |
| `tag` | resolve が EAST2 に付与する semantic_tag | 必須 |

### 10.5 処理の流れ

1. **parse**: `extern_fn` / `extern_var` / `extern_class` の引数を読み、EAST1 の meta に `extern_v2: {module, symbol, tag}` として格納
2. **resolve**: meta から module/symbol/tag を取り、EAST2 ノードに `runtime_module_id` / `runtime_symbol` / `semantic_tag` を付与
3. **emitter**: 解決済み属性を見て各言語に写像するだけ

### 10.6 必須性

v2 では `module`, `symbol`, `tag` を **全て必須** とする。理由:
- 省略すると resolve がハードコードや推測に頼ることになり、§5.7（ハードコードテーブル禁止）に反する
- 明示的に書くことで、宣言ファイルだけ読めば runtime 配置が完全に分かる
- emitter が extern を見て「module/symbol がないから何もできない」という状態を防ぐ

### 10.7 v1 との関係

- v1（`@extern` 引数なし）は現行 `src/pytra/std/` で引き続き使用
- v2（`extern_fn` / `extern_var` / `extern_class`）は `src/include/py/pytra/` で使用
- `toolchain2/` のコードでは v2 を必須とする

### 10.8 メリット

- ハードコードテーブルが不要になる（`builtin_registry.py` の 4 テーブルを除去可能）
- built-in / stdlib の追加・変更が宣言ファイルの編集だけで完結
- ユーザーも同じ仕組みで独自の extern を定義可能
- runtime 情報が宣言ファイルに 1 箇所で集約され、全 emitter で共有される
- 用途別に分離することで Pylance の型チェックが正しく動く

## 11. 未決事項

- ~~`object` を引数型にしてよいか~~ → `Obj` 型で解決。`object` は使わない。
- ~~ジェネリック型パラメータ `T` の表現~~ → `@template` をクラスにも適用。
- ~~`print` の可変長引数 `*args` の扱い~~ → `*args: T` を `args: list[T]` に resolve が変換。
- ~~`range` のオーバーロード~~ → resolve が `start/stop/step` に正規化し `ForRange` / `RangeExpr` に変換。emitter には届かない。
- ~~dunder 展開のタイミング~~ → resolve が `len(x)` → `py_len(x)` 等のノードに変換。dunder 展開はしない（型チェックのみ）。emitter は `py_len` を各言語 runtime に写像。
- ~~`min`/`max` の引数が 2 個以上の場合~~ → varargs（`*args: T` → `list[T]`）。optimize が要素数 2 を特殊化してもよい。
- ~~`int(x, base=16)` の base 引数~~ → 当面サポートしない。必要になったら別関数として追加。
- ~~コンテナ型の宣言の配置場所~~ → `src/pytra/built_in/` に配置。`pytra: builtin-declarations` ディレクティブ付き。
