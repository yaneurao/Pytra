"""Pytra stdlib declarations."""


def extern(obj=None, *, module: str = "", symbol: str = "", tag: str = ""):
    """外部実装宣言または no-op wrapper。"""
    if module != "" or symbol != "" or tag != "":
        def deco(fn):
            return fn
        return deco
    return obj


def extern_fn(*, module: str, symbol: str, tag: str):
    """外部関数宣言。decorator として使う。"""
    return extern(module=module, symbol=symbol, tag=tag)


def extern_var(*, module: str, symbol: str, tag: str):
    """外部変数宣言。型注釈に従う値を返す（実行時は None）。"""
    return None


def extern_class(*, module: str, symbol: str, tag: str):
    """外部クラス宣言。decorator として使う。"""
    def deco(cls):
        return cls
    return deco


def runtime(namespace: str, *, symbol: str = "", tag: str = ""):
    """runtime 実装クラス・関数宣言。decorator として使う。"""
    def deco(obj):
        return obj
    return deco


def template(*params):
    def deco(fn):
        return fn
    return deco
