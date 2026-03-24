"""Pytra stdlib declarations (v2 extern)."""


def extern_fn(*, module: str, symbol: str, tag: str):
    """外部関数宣言。decorator として使う。"""
    def deco(fn):
        return fn
    return deco


def extern_var(*, module: str, symbol: str, tag: str):
    """外部変数宣言。型注釈に従う値を返す（実行時は None）。"""
    return None


def extern_class(*, module: str, symbol: str, tag: str):
    """外部クラス宣言。decorator として使う。"""
    def deco(cls):
        return cls
    return deco


def extern_method(*, module: str, symbol: str, tag: str):
    """外部メソッド宣言。クラス内メソッドの decorator として使う。"""
    def deco(fn):
        return fn
    return deco


def abi(*, args=None, ret="default"):
    def deco(fn):
        return fn
    return deco


def template(*params):
    def deco(fn):
        return fn
    return deco
