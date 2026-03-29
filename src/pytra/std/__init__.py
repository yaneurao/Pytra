"""Python stdlib compatibility modules for Pytra."""


def extern(obj=None, *, module: str = "", symbol: str = "", tag: str = ""):
    if module != "" or symbol != "" or tag != "":
        def deco(fn):
            return fn
        return deco
    return obj


def runtime(namespace: str):
    def deco(cls):
        return cls
    return deco


def template(*params):
    def deco(fn):
        return fn

    return deco
