"""Pure-Python source-of-truth for single-inheritance type_id range semantics."""

from pytra.std.typing import Any


_TYPE_IDS: list[int] = []
_TYPE_BASE: dict[int, int] = {}
_TYPE_CHILDREN: dict[int, list[int]] = {}
_TYPE_ORDER: dict[int, int] = {}
_TYPE_MIN: dict[int, int] = {}
_TYPE_MAX: dict[int, int] = {}
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


def _contains_int(items: list[int], value: int) -> bool:
    i = 0
    while i < len(items):
        if items[i] == value:
            return True
        i += 1
    return False


def _copy_int_list(items: list[int]) -> list[int]:
    out: list[int] = []
    i = 0
    while i < len(items):
        out.append(items[i])
        i += 1
    return out


def _sorted_ints(items: list[int]) -> list[int]:
    out = _copy_int_list(items)
    i = 0
    while i < len(out):
        j = i + 1
        while j < len(out):
            if out[j] < out[i]:
                tmp = out[i]
                out[i] = out[j]
                out[j] = tmp
            j += 1
        i += 1
    return out


def _register_type_node(type_id: int, base_type_id: int) -> None:
    if not _contains_int(_TYPE_IDS, type_id):
        _TYPE_IDS.append(type_id)
    _TYPE_BASE[type_id] = base_type_id
    if type_id not in _TYPE_CHILDREN:
        _TYPE_CHILDREN[type_id] = _make_int_list_0()
    if base_type_id < 0:
        return
    if base_type_id not in _TYPE_CHILDREN:
        _TYPE_CHILDREN[base_type_id] = _make_int_list_0()
    children = _TYPE_CHILDREN[base_type_id]
    if not _contains_int(children, type_id):
        children.append(type_id)


def _sorted_child_type_ids(type_id: int) -> list[int]:
    children = _make_int_list_0()
    if type_id in _TYPE_CHILDREN:
        children = _TYPE_CHILDREN[type_id]
    return _sorted_ints(children)


def _collect_root_type_ids() -> list[int]:
    roots: list[int] = []
    i = 0
    while i < len(_TYPE_IDS):
        tid = _TYPE_IDS[i]
        base_tid = -1
        if tid in _TYPE_BASE:
            base_tid = _TYPE_BASE[tid]
        if base_tid < 0 or base_tid not in _TYPE_BASE:
            roots.append(tid)
        i += 1
    return _sorted_ints(roots)


def _assign_type_ranges_dfs(type_id: int, next_order: int) -> int:
    _TYPE_ORDER[type_id] = next_order
    _TYPE_MIN[type_id] = next_order
    cur = next_order + 1
    children = _sorted_child_type_ids(type_id)
    i = 0
    while i < len(children):
        cur = _assign_type_ranges_dfs(children[i], cur)
        i += 1
    _TYPE_MAX[type_id] = cur - 1
    return cur


def _recompute_type_ranges() -> None:
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()

    next_order = 0
    roots = _collect_root_type_ids()
    i = 0
    while i < len(roots):
        next_order = _assign_type_ranges_dfs(roots[i], next_order)
        i += 1

    all_ids = _sorted_ints(_TYPE_IDS)
    i = 0
    while i < len(all_ids):
        tid = all_ids[i]
        if tid not in _TYPE_ORDER:
            next_order = _assign_type_ranges_dfs(tid, next_order)
        i += 1


def _ensure_builtins() -> None:
    if "next_user_type_id" not in _TYPE_STATE:
        _TYPE_STATE["next_user_type_id"] = _tid_user_base()
    if len(_TYPE_IDS) > 0:
        return

    _register_type_node(_tid_none(), -1)
    _register_type_node(_tid_object(), -1)
    _register_type_node(_tid_int(), _tid_object())
    _register_type_node(_tid_bool(), _tid_int())
    _register_type_node(_tid_float(), _tid_object())
    _register_type_node(_tid_str(), _tid_object())
    _register_type_node(_tid_list(), _tid_object())
    _register_type_node(_tid_dict(), _tid_object())
    _register_type_node(_tid_set(), _tid_object())
    _recompute_type_ranges()


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
    if len(out) > 1:
        raise ValueError("multiple inheritance is not supported")
    if out[0] not in _TYPE_BASE:
        raise ValueError("unknown base type_id: " + str(out[0]))
    return out


def py_tid_register_class_type(base_type_ids: list[int]) -> int:
    """Allocate and register a new user class type_id."""
    _ensure_builtins()
    bases = _normalize_base_type_ids(base_type_ids)
    base_tid = bases[0]

    tid = _TYPE_STATE["next_user_type_id"]
    while tid in _TYPE_BASE:
        tid += 1
    _TYPE_STATE["next_user_type_id"] = tid + 1

    _register_type_node(tid, base_tid)
    _recompute_type_ranges()
    return tid


def _try_runtime_tagged_type_id(value: Any) -> int:
    tagged = getattr(value, "PYTRA_TYPE_ID", None)
    if isinstance(tagged, int):
        if tagged in _TYPE_BASE:
            return tagged
    return -1


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
    tagged = _try_runtime_tagged_type_id(value)
    if tagged >= 0:
        return tagged
    return _tid_object()


def py_tid_is_subtype(actual_type_id: int, expected_type_id: int) -> bool:
    """Check nominal subtype relation by type_id order range."""
    _ensure_builtins()
    if actual_type_id not in _TYPE_ORDER:
        return False
    if expected_type_id not in _TYPE_ORDER:
        return False
    actual_order = _TYPE_ORDER[actual_type_id]
    expected_min = _TYPE_MIN[expected_type_id]
    expected_max = _TYPE_MAX[expected_type_id]
    return expected_min <= actual_order and actual_order <= expected_max


def py_tid_issubclass(actual_type_id: int, expected_type_id: int) -> bool:
    return py_tid_is_subtype(actual_type_id, expected_type_id)


def py_tid_isinstance(value: Any, expected_type_id: int) -> bool:
    return py_tid_is_subtype(py_tid_runtime_type_id(value), expected_type_id)


def _py_reset_type_registry_for_test() -> None:
    """Reset mutable registry state for deterministic unit tests."""
    _TYPE_IDS.clear()
    _TYPE_BASE.clear()
    _TYPE_CHILDREN.clear()
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    _TYPE_STATE.clear()
    _TYPE_STATE["next_user_type_id"] = _tid_user_base()
    _ensure_builtins()
