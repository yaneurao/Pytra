"""Minimal dataclasses shim for selfhost-friendly code."""

from __future__ import annotations

from pylib.std.typing import Any


def dataclass(_cls: type[Any] | None = None, **kwargs: Any):
    """`@dataclass` の最小互換実装。

    対応:
    - init/repr/eq（既定 True）
    - フィールド順は `__annotations__` の定義順
    - 既定値はクラス属性から取得
    """

    init_enabled = bool(kwargs.get("init", True))
    repr_enabled = bool(kwargs.get("repr", True))
    eq_enabled = bool(kwargs.get("eq", True))

    def wrap(cls: type[Any]) -> type[Any]:
        anns = getattr(cls, "__annotations__", {})
        fields: list[str] = []
        if isinstance(anns, dict):
            for name in anns.keys():
                if isinstance(name, str):
                    fields.append(name)

        defaults: dict[str, Any] = {}
        for name in fields:
            if hasattr(cls, name):
                defaults[name] = getattr(cls, name)

        if init_enabled:
            def __init__(self, *args: Any, **kw: Any) -> None:
                if len(args) > len(fields):
                    raise TypeError(f"{cls.__name__}() takes {len(fields)} positional arguments but {len(args)} were given")
                vals: dict[str, Any] = {}
                i = 0
                while i < len(fields):
                    name = fields[i]
                    if i < len(args):
                        vals[name] = args[i]
                    elif name in kw:
                        vals[name] = kw.pop(name)
                    elif name in defaults:
                        vals[name] = defaults[name]
                    else:
                        raise TypeError(f"{cls.__name__}() missing required argument: '{name}'")
                    i += 1
                if len(kw) != 0:
                    extra = ",".join(str(k) for k in kw.keys())
                    raise TypeError(f"{cls.__name__}() got unexpected keyword arguments: {extra}")
                for name in fields:
                    setattr(self, name, vals[name])

            setattr(cls, "__init__", __init__)

        if repr_enabled:
            def __repr__(self) -> str:
                parts: list[str] = []
                for name in fields:
                    parts.append(f"{name}={getattr(self, name)!r}")
                return f"{cls.__name__}(" + ", ".join(parts) + ")"

            setattr(cls, "__repr__", __repr__)

        if eq_enabled:
            def __eq__(self, other: Any) -> bool:
                if other.__class__ is not cls:
                    return False
                for name in fields:
                    if getattr(self, name) != getattr(other, name):
                        return False
                return True

            setattr(cls, "__eq__", __eq__)

        return cls

    if _cls is None:
        return wrap
    return wrap(_cls)

