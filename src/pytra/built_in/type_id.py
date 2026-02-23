"""Pure-Python source-of-truth for type_id based subtype/isinstance semantics."""

from pytra.std.typing import Any


_TYPE_BASES: dict[int, list[int]] = {}
_TYPE_STATE: dict[str, int] = {}


def _tid_none() -> int:
    return 0


def _tid_bool() -> int:
    return 1


def _tid_int() -> int:
    return 2


def _tid_float() -> int:
    return 3


def _tid_str() -> int:
    return 4


def _tid_list() -> int:
    return 5


def _tid_dict() -> int:
    return 6


def _tid_set() -> int:
    return 7


def _tid_object() -> int:
    return 8


def _tid_user_base() -> int:
    return 1000


def _make_int_list_0() -> list[int]:
    out: list[int] = []
    return out


def _make_int_list_1(a0: int) -> list[int]:
    out: list[int] = []
    out.append(a0)
    return out


def _make_int_list_2(a0: int, a1: int) -> list[int]:
    out: list[int] = []
    out.append(a0)
    out.append(a1)
    return out


def _contains_int(items: list[int], value: int) -> bool:
    i = 0
    while i < len(items):
        if items[i] == value:
            return True
        i += 1
    return False


def _ensure_builtins() -> None:
    if "next_user_type_id" not in _TYPE_STATE:
        _TYPE_STATE["next_user_type_id"] = _tid_user_base()
    if len(_TYPE_BASES) > 0:
        return
    _TYPE_BASES[_tid_none()] = _make_int_list_0()
    _TYPE_BASES[_tid_object()] = _make_int_list_0()
    _TYPE_BASES[_tid_bool()] = _make_int_list_2(_tid_int(), _tid_object())
    _TYPE_BASES[_tid_int()] = _make_int_list_1(_tid_object())
    _TYPE_BASES[_tid_float()] = _make_int_list_1(_tid_object())
    _TYPE_BASES[_tid_str()] = _make_int_list_1(_tid_object())
    _TYPE_BASES[_tid_list()] = _make_int_list_1(_tid_object())
    _TYPE_BASES[_tid_dict()] = _make_int_list_1(_tid_object())
    _TYPE_BASES[_tid_set()] = _make_int_list_1(_tid_object())


def _normalize_base_type_ids(base_type_ids: list[int]) -> list[int]:
    _ensure_builtins()
    out: list[int] = []
    i = 0
    while i < len(base_type_ids):
        tid = base_type_ids[i]
        if isinstance(tid, int):
            if not _contains_int(out, tid):
                out.append(tid)
        i += 1
    if len(out) == 0:
        out.append(_tid_object())
    return out


def py_tid_register_class_type(base_type_ids: list[int]) -> int:
    """Allocate and register a new user class type_id."""
    _ensure_builtins()
    tid = _TYPE_STATE["next_user_type_id"]
    _TYPE_STATE["next_user_type_id"] = tid + 1
    _TYPE_BASES[tid] = _normalize_base_type_ids(base_type_ids)
    return tid


def py_tid_runtime_type_id(value: Any) -> int:
    """Resolve runtime type_id for a Python value."""
    _ensure_builtins()
    if value is None:
        return _tid_none()
    if isinstance(value, bool):
        return _tid_bool()
    if isinstance(value, int):
        return _tid_int()
    if isinstance(value, float):
        return _tid_float()
    if isinstance(value, str):
        return _tid_str()
    if isinstance(value, list):
        return _tid_list()
    if isinstance(value, dict):
        return _tid_dict()
    if isinstance(value, set):
        return _tid_set()
    return _tid_object()


def py_tid_is_subtype(actual_type_id: int, expected_type_id: int) -> bool:
    """Check nominal subtype relation by walking base type graph."""
    _ensure_builtins()
    if actual_type_id == expected_type_id:
        return True
    if expected_type_id == _tid_object() and actual_type_id != _tid_none():
        return True

    stack: list[int] = _make_int_list_1(actual_type_id)
    visited: list[int] = _make_int_list_0()
    while len(stack) > 0:
        cur = stack.pop()
        if cur == expected_type_id:
            return True
        if _contains_int(visited, cur):
            continue
        visited.append(cur)
        bases: list[int] = _make_int_list_0()
        if cur in _TYPE_BASES:
            bases = _TYPE_BASES[cur]
        i = 0
        while i < len(bases):
            base_tid = bases[i]
            if not _contains_int(visited, base_tid):
                stack.append(base_tid)
            i += 1
    return False


def py_tid_issubclass(actual_type_id: int, expected_type_id: int) -> bool:
    return py_tid_is_subtype(actual_type_id, expected_type_id)


def py_tid_isinstance(value: Any, expected_type_id: int) -> bool:
    return py_tid_is_subtype(py_tid_runtime_type_id(value), expected_type_id)


def _py_reset_type_registry_for_test() -> None:
    """Reset mutable registry state for deterministic unit tests."""
    _TYPE_BASES.clear()
    _TYPE_STATE["next_user_type_id"] = _tid_user_base()
    _ensure_builtins()
