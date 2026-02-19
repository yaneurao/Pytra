"""Minimal enum shim for transpile target code."""

from __future__ import annotations

from pylib.std.typing import Any


class EnumMeta(type):
    """Collect enum members at class creation and bind instances."""

    def __new__(mcls, name: str, bases: tuple[type[Any], ...], ns: dict[str, Any]):
        cls = super().__new__(mcls, name, bases, ns)
        member_map: dict[str, Any] = {}
        value_map: dict[Any, Any] = {}

        for k, v in list(ns.items()):
            if k.startswith("_"):
                continue
            if callable(v):
                continue
            if isinstance(v, (staticmethod, classmethod, property)):
                continue
            member = cls._from_value(v, k)
            setattr(cls, k, member)
            member_map[k] = member
            value_map[getattr(member, "value", v)] = member

        cls._member_map_ = member_map
        cls._value2member_map_ = value_map
        return cls

    def __iter__(cls):
        return iter(cls._member_map_.values())

    def __call__(cls, value: Any):
        if value in cls._value2member_map_:
            return cls._value2member_map_[value]
        raise ValueError(f"{cls.__name__}: unknown value {value!r}")


class Enum(metaclass=EnumMeta):
    _member_map_: dict[str, "Enum"] = {}
    _value2member_map_: dict[Any, "Enum"] = {}

    @classmethod
    def _from_value(cls, value: Any, name: str = "") -> "Enum":
        obj = object.__new__(cls)
        obj._name_ = name
        obj._value_ = value
        return obj

    @property
    def name(self) -> str:
        return self._name_

    @property
    def value(self) -> Any:
        return self._value_

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._name_}"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self._value_ == other._value_

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self._value_))


class IntEnum(int, Enum):
    @classmethod
    def _from_value(cls, value: Any, name: str = "") -> "IntEnum":
        iv = int(value)
        obj = int.__new__(cls, iv)
        obj._name_ = name
        obj._value_ = iv
        return obj

    def __str__(self) -> str:
        return str(int(self))


class IntFlag(IntEnum):
    @classmethod
    def _coerce_or_make(cls, iv: int) -> "IntFlag":
        if iv in cls._value2member_map_:
            return cls._value2member_map_[iv]
        obj = int.__new__(cls, iv)
        obj._name_ = str(iv)
        obj._value_ = iv
        return obj

    def __or__(self, other: Any) -> "IntFlag":
        return self.__class__._coerce_or_make(int(self) | int(other))

    def __and__(self, other: Any) -> "IntFlag":
        return self.__class__._coerce_or_make(int(self) & int(other))

    def __xor__(self, other: Any) -> "IntFlag":
        return self.__class__._coerce_or_make(int(self) ^ int(other))

    def __invert__(self) -> "IntFlag":
        return self.__class__._coerce_or_make(~int(self))

