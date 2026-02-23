"""Pure-Python source-of-truth for type_id based subtype/isinstance semantics."""

from pytra.std.typing import Any


PYTRA_TID_NONE = 0
PYTRA_TID_BOOL = 1
PYTRA_TID_INT = 2
PYTRA_TID_FLOAT = 3
PYTRA_TID_STR = 4
PYTRA_TID_LIST = 5
PYTRA_TID_DICT = 6
PYTRA_TID_SET = 7
PYTRA_TID_OBJECT = 8
PYTRA_TID_USER_BASE = 1000


_TYPE_BASES: dict[int, list[int]] = {}
_TYPE_STATE: dict[str, int] = {"next_user_type_id": PYTRA_TID_USER_BASE}


def _contains_int(items: list[int], value: int) -> bool:
    i = 0
    while i < len(items):
        if items[i] == value:
            return True
        i += 1
    return False


def _ensure_builtins() -> None:
    if len(_TYPE_BASES) > 0:
        return
    _TYPE_BASES[PYTRA_TID_NONE] = []
    _TYPE_BASES[PYTRA_TID_OBJECT] = []
    _TYPE_BASES[PYTRA_TID_BOOL] = [PYTRA_TID_INT, PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_INT] = [PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_FLOAT] = [PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_STR] = [PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_LIST] = [PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_DICT] = [PYTRA_TID_OBJECT]
    _TYPE_BASES[PYTRA_TID_SET] = [PYTRA_TID_OBJECT]


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
        out.append(PYTRA_TID_OBJECT)
    return out


def py_register_class_type(base_type_ids: list[int]) -> int:
    """Allocate and register a new user class type_id."""
    _ensure_builtins()
    tid = _TYPE_STATE["next_user_type_id"]
    _TYPE_STATE["next_user_type_id"] = tid + 1
    _TYPE_BASES[tid] = _normalize_base_type_ids(base_type_ids)
    return tid


def py_runtime_type_id(value: Any) -> int:
    """Resolve runtime type_id for a Python value."""
    _ensure_builtins()
    if value is None:
        return PYTRA_TID_NONE
    if isinstance(value, bool):
        return PYTRA_TID_BOOL
    if isinstance(value, int):
        return PYTRA_TID_INT
    if isinstance(value, float):
        return PYTRA_TID_FLOAT
    if isinstance(value, str):
        return PYTRA_TID_STR
    if isinstance(value, list):
        return PYTRA_TID_LIST
    if isinstance(value, dict):
        return PYTRA_TID_DICT
    if isinstance(value, set):
        return PYTRA_TID_SET

    py_type_id = getattr(value, "py_type_id", None)
    if isinstance(py_type_id, int):
        return py_type_id

    cls_type_id = getattr(type(value), "PYTRA_TYPE_ID", None)
    if isinstance(cls_type_id, int):
        return cls_type_id

    return PYTRA_TID_OBJECT


def py_is_subtype(actual_type_id: int, expected_type_id: int) -> bool:
    """Check nominal subtype relation by walking base type graph."""
    _ensure_builtins()
    if actual_type_id == expected_type_id:
        return True
    if expected_type_id == PYTRA_TID_OBJECT and actual_type_id != PYTRA_TID_NONE:
        return True

    stack: list[int] = [actual_type_id]
    visited: list[int] = []
    while len(stack) > 0:
        cur = stack.pop()
        if cur == expected_type_id:
            return True
        if _contains_int(visited, cur):
            continue
        visited.append(cur)
        bases = _TYPE_BASES[cur] if cur in _TYPE_BASES else []
        i = 0
        while i < len(bases):
            base_tid = bases[i]
            if not _contains_int(visited, base_tid):
                stack.append(base_tid)
            i += 1
    return False


def py_issubclass(actual_type_id: int, expected_type_id: int) -> bool:
    return py_is_subtype(actual_type_id, expected_type_id)


def py_isinstance(value: Any, expected_type_id: int) -> bool:
    return py_is_subtype(py_runtime_type_id(value), expected_type_id)


def _py_reset_type_registry_for_test() -> None:
    """Reset mutable registry state for deterministic unit tests."""
    _TYPE_BASES.clear()
    _TYPE_STATE["next_user_type_id"] = PYTRA_TID_USER_BASE
    _ensure_builtins()
