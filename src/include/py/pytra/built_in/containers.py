# pytra: builtin-declarations
"""コンテナ型の dunder + メソッド宣言。

resolve がメソッドシグネチャ + meta.extern_v2 を参照して型解決する。emit 対象外。
@template でクラスレベル型パラメータを宣言する。
引数の型は exact match（暗黙変換なし）。

spec: docs/ja/spec/spec-builtin-functions.md §4, §10
"""

from pytra.std import template, extern_class, extern_method


# ---------------------------------------------------------------------------
# Iterable[T] — for ループの __iter__ 戻り値型
# ---------------------------------------------------------------------------

@template("T")
class Iterable:
    ...


# ---------------------------------------------------------------------------
# §4.1 list
# ---------------------------------------------------------------------------

@template("T")
@extern_class(module="pytra.core.list", symbol="list", tag="container.list")
class list:
    @extern_method(module="pytra.core.list", symbol="list.__len__", tag="dunder.len")
    def __len__(self) -> int: ...

    @extern_method(module="pytra.core.list", symbol="list.__str__", tag="dunder.str")
    def __str__(self) -> str: ...

    @extern_method(module="pytra.core.list", symbol="list.__bool__", tag="dunder.bool")
    def __bool__(self) -> bool: ...

    @extern_method(module="pytra.core.list", symbol="list.__iter__", tag="dunder.iter")
    def __iter__(self) -> Iterable[T]: ...

    @extern_method(module="pytra.core.list", symbol="list.append", tag="stdlib.method.append")
    def append(self, x: T) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.extend", tag="stdlib.method.extend")
    def extend(self, x: list[T]) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.pop", tag="stdlib.method.pop")
    def pop(self, index: int = -1) -> T: ...

    @extern_method(module="pytra.core.list", symbol="list.insert", tag="stdlib.method.insert")
    def insert(self, index: int, x: T) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.remove", tag="stdlib.method.remove")
    def remove(self, x: T) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.clear", tag="stdlib.method.clear")
    def clear(self) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.reverse", tag="stdlib.method.reverse")
    def reverse(self) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.sort", tag="stdlib.method.sort")
    def sort(self) -> None: ...

    @extern_method(module="pytra.core.list", symbol="list.copy", tag="stdlib.method.copy")
    def copy(self) -> list[T]: ...

    @extern_method(module="pytra.core.list", symbol="list.index", tag="stdlib.method.index")
    def index(self, x: T) -> int: ...

    @extern_method(module="pytra.core.list", symbol="list.count", tag="stdlib.method.count")
    def count(self, x: T) -> int: ...


# ---------------------------------------------------------------------------
# §4.2 str
# ---------------------------------------------------------------------------

@extern_class(module="pytra.core.str", symbol="str", tag="container.str")
class str:
    @extern_method(module="pytra.core.str", symbol="str.__len__", tag="dunder.len")
    def __len__(self) -> int: ...

    @extern_method(module="pytra.core.str", symbol="str.__str__", tag="dunder.str")
    def __str__(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.__bool__", tag="dunder.bool")
    def __bool__(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.__int__", tag="dunder.int")
    def __int__(self) -> int: ...

    @extern_method(module="pytra.core.str", symbol="str.__float__", tag="dunder.float")
    def __float__(self) -> float: ...

    @extern_method(module="pytra.core.str", symbol="str.upper", tag="stdlib.method.upper")
    def upper(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.lower", tag="stdlib.method.lower")
    def lower(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.strip", tag="stdlib.method.strip")
    def strip(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.lstrip", tag="stdlib.method.lstrip")
    def lstrip(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.rstrip", tag="stdlib.method.rstrip")
    def rstrip(self) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.split", tag="stdlib.method.split")
    def split(self, sep: str = " ") -> list[str]: ...

    @extern_method(module="pytra.core.str", symbol="str.join", tag="stdlib.method.join")
    def join(self, parts: list[str]) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.startswith", tag="stdlib.method.startswith")
    def startswith(self, prefix: str) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.endswith", tag="stdlib.method.endswith")
    def endswith(self, suffix: str) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.find", tag="stdlib.method.find")
    def find(self, sub: str) -> int: ...

    @extern_method(module="pytra.core.str", symbol="str.rfind", tag="stdlib.method.rfind")
    def rfind(self, sub: str) -> int: ...

    @extern_method(module="pytra.core.str", symbol="str.replace", tag="stdlib.method.replace")
    def replace(self, old: str, new: str) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.isdigit", tag="stdlib.method.isdigit")
    def isdigit(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.isalpha", tag="stdlib.method.isalpha")
    def isalpha(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.isalnum", tag="stdlib.method.isalnum")
    def isalnum(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.isupper", tag="stdlib.method.isupper")
    def isupper(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.islower", tag="stdlib.method.islower")
    def islower(self) -> bool: ...

    @extern_method(module="pytra.core.str", symbol="str.zfill", tag="stdlib.method.zfill")
    def zfill(self, width: int) -> str: ...

    @extern_method(module="pytra.core.str", symbol="str.count", tag="stdlib.method.count")
    def count(self, sub: str) -> int: ...


# ---------------------------------------------------------------------------
# §4.3 dict
# ---------------------------------------------------------------------------

@template("K", "V")
@extern_class(module="pytra.core.dict", symbol="dict", tag="container.dict")
class dict:
    @extern_method(module="pytra.core.dict", symbol="dict.__len__", tag="dunder.len")
    def __len__(self) -> int: ...

    @extern_method(module="pytra.core.dict", symbol="dict.__str__", tag="dunder.str")
    def __str__(self) -> str: ...

    @extern_method(module="pytra.core.dict", symbol="dict.__bool__", tag="dunder.bool")
    def __bool__(self) -> bool: ...

    @extern_method(module="pytra.core.dict", symbol="dict.keys", tag="stdlib.method.keys")
    def keys(self) -> list[K]: ...

    @extern_method(module="pytra.core.dict", symbol="dict.values", tag="stdlib.method.values")
    def values(self) -> list[V]: ...

    @extern_method(module="pytra.core.dict", symbol="dict.items", tag="stdlib.method.items")
    def items(self) -> list[tuple[K, V]]: ...

    @extern_method(module="pytra.core.dict", symbol="dict.get", tag="stdlib.method.get")
    def get(self, key: K, default: V = None) -> V: ...

    @extern_method(module="pytra.core.dict", symbol="dict.pop", tag="stdlib.method.pop")
    def pop(self, key: K) -> V: ...

    @extern_method(module="pytra.core.dict", symbol="dict.setdefault", tag="stdlib.method.setdefault")
    def setdefault(self, key: K, default: V = None) -> V: ...

    @extern_method(module="pytra.core.dict", symbol="dict.clear", tag="stdlib.method.clear")
    def clear(self) -> None: ...

    @extern_method(module="pytra.core.dict", symbol="dict.update", tag="stdlib.method.update")
    def update(self, other: dict[K, V]) -> None: ...


# ---------------------------------------------------------------------------
# §4.4 set
# ---------------------------------------------------------------------------

@template("T")
@extern_class(module="pytra.core.set", symbol="set", tag="container.set")
class set:
    @extern_method(module="pytra.core.set", symbol="set.__len__", tag="dunder.len")
    def __len__(self) -> int: ...

    @extern_method(module="pytra.core.set", symbol="set.__str__", tag="dunder.str")
    def __str__(self) -> str: ...

    @extern_method(module="pytra.core.set", symbol="set.__bool__", tag="dunder.bool")
    def __bool__(self) -> bool: ...

    @extern_method(module="pytra.core.set", symbol="set.add", tag="stdlib.method.add")
    def add(self, x: T) -> None: ...

    @extern_method(module="pytra.core.set", symbol="set.discard", tag="stdlib.method.discard")
    def discard(self, x: T) -> None: ...

    @extern_method(module="pytra.core.set", symbol="set.remove", tag="stdlib.method.remove")
    def remove(self, x: T) -> None: ...

    @extern_method(module="pytra.core.set", symbol="set.clear", tag="stdlib.method.clear")
    def clear(self) -> None: ...


# ---------------------------------------------------------------------------
# §4.5 tuple
# ---------------------------------------------------------------------------

@extern_class(module="pytra.core.tuple", symbol="tuple", tag="container.tuple")
class tuple:
    @extern_method(module="pytra.core.tuple", symbol="tuple.__len__", tag="dunder.len")
    def __len__(self) -> int: ...

    @extern_method(module="pytra.core.tuple", symbol="tuple.__str__", tag="dunder.str")
    def __str__(self) -> str: ...

    @extern_method(module="pytra.core.tuple", symbol="tuple.__bool__", tag="dunder.bool")
    def __bool__(self) -> bool: ...
