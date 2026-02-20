"""Minimal dataclasses shim for selfhost-friendly code.

Design notes:
- self_hosted parser で扱える構文のみを使う。
- ネスト def / *args / **kwargs を使わない。
- 本実装は本リポジトリで必要な最小互換（init/repr/eq）を提供する。
"""

from __future__ import annotations

from pytra.std.typing import Any

_MISSING: Any = object()


def _collect_fields(cls: type[Any]) -> list[str]:
    anns = getattr(cls, "__annotations__", {})
    out: list[str] = []
    if isinstance(anns, dict):
        for name in anns.keys():
            if isinstance(name, str):
                out.append(name)
    return out


def _collect_defaults(cls: type[Any], fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in fields:
        if hasattr(cls, name):
            out[name] = getattr(cls, name)
    return out


def _make_init(cls_name: str, fields: list[str], defaults: dict[str, Any]) -> Any:
    sig_parts: list[str] = []
    for name in fields:
        sig_parts.append(name + "=_MISSING")
    sig_txt = ""
    if len(sig_parts) > 0:
        sig_txt = ", " + ", ".join(sig_parts)

    lines: list[str] = []
    lines.append("def __init__(self" + sig_txt + "):")
    if len(fields) == 0:
        lines.append("    return None")
    else:
        for name in fields:
            lines.append("    if " + name + " is _MISSING:")
            lines.append("        if '" + name + "' in _defaults:")
            lines.append("            " + name + " = _defaults['" + name + "']")
            lines.append("        else:")
            lines.append("            raise TypeError(_cls_name + \"() missing required argument: '" + name + "'\")")
        for name in fields:
            lines.append("    self." + name + " = " + name)
    src = "\n".join(lines) + "\n"
    scope: dict[str, Any] = {
        "_MISSING": _MISSING,
        "_defaults": defaults,
        "_cls_name": cls_name,
        "TypeError": TypeError,
    }
    exec(src, scope)
    return scope["__init__"]


def _dc_repr(self: Any) -> str:
    cls = getattr(self, "__class__", None)
    fields_any = getattr(cls, "__pytra_dc_fields__", [])
    fields: list[str] = fields_any if isinstance(fields_any, list) else []
    parts: list[str] = []
    for name in fields:
        parts.append(name + "=" + repr(getattr(self, name)))
    cls_name_any = getattr(cls, "__name__", "Dataclass")
    cls_name = str(cls_name_any)
    return cls_name + "(" + ", ".join(parts) + ")"


def _dc_eq(self: Any, other: Any) -> bool:
    cls = getattr(self, "__class__", None)
    other_cls = getattr(other, "__class__", None)
    if other_cls is not cls:
        return False
    fields_any = getattr(cls, "__pytra_dc_fields__", [])
    fields: list[str] = fields_any if isinstance(fields_any, list) else []
    for name in fields:
        if getattr(self, name) != getattr(other, name):
            return False
    return True


def _apply_dataclass(
    cls: type[Any],
    init_enabled: bool,
    repr_enabled: bool,
    eq_enabled: bool,
) -> type[Any]:
    fields = _collect_fields(cls)
    defaults = _collect_defaults(cls, fields)
    setattr(cls, "__pytra_dc_fields__", fields)
    setattr(cls, "__pytra_dc_defaults__", defaults)
    if init_enabled:
        cls_name_any = getattr(cls, "__name__", "Dataclass")
        setattr(cls, "__init__", _make_init(str(cls_name_any), fields, defaults))
    if repr_enabled:
        setattr(cls, "__repr__", _dc_repr)
    if eq_enabled:
        setattr(cls, "__eq__", _dc_eq)
    return cls


class _DataclassConfig:
    init_enabled: bool
    repr_enabled: bool
    eq_enabled: bool

    def __init__(self, init_enabled: bool, repr_enabled: bool, eq_enabled: bool) -> None:
        self.init_enabled = init_enabled
        self.repr_enabled = repr_enabled
        self.eq_enabled = eq_enabled

    def __call__(self, cls: type[Any]) -> type[Any]:
        return _apply_dataclass(cls, self.init_enabled, self.repr_enabled, self.eq_enabled)


def dataclass(
    _cls: type[Any] | None = None,
    init: bool = True,
    repr: bool = True,
    eq: bool = True,
) -> Any:
    """`@dataclass` の最小互換実装。"""
    if _cls is None:
        return _DataclassConfig(init, repr, eq)
    return _apply_dataclass(_cls, init, repr, eq)
