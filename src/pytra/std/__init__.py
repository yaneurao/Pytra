"""Python stdlib compatibility modules for Pytra."""


def extern(fn):
    return fn


def abi(*, args=None, ret="default"):
    def deco(fn):
        return fn

    return deco
