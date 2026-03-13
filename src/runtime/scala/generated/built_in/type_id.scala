// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

import scala.collection.mutable
import scala.util.boundary, boundary.break
import java.nio.file.{Files, Paths}


def _tid_none(): Long = {
    return 0L
}

def _tid_bool(): Long = {
    return 1L
}

def _tid_int(): Long = {
    return 2L
}

def _tid_float(): Long = {
    return 3L
}

def _tid_str(): Long = {
    return 4L
}

def _tid_list(): Long = {
    return 5L
}

def _tid_dict(): Long = {
    return 6L
}

def _tid_set(): Long = {
    return 7L
}

def _tid_object(): Long = {
    return 8L
}

def _tid_user_base(): Long = {
    return 1000L
}

def _make_int_list_0(): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    return out
}

def _make_int_list_1(a0: Long): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    out.append(a0)
    return out
}

def _contains_int(items: mutable.ArrayBuffer[Long], value: Long): Boolean = {
    var i: Long = 0L
    while (i < __pytra_len(items)) {
        if (__pytra_int(__pytra_get_index(items, i)) == value) {
            return true
        }
        i += 1L
    }
    return false
}

def _copy_int_list(items: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    var i: Long = 0L
    while (i < __pytra_len(items)) {
        out.append(__pytra_int(__pytra_get_index(items, i)))
        i += 1L
    }
    return out
}

def _sorted_ints(items: mutable.ArrayBuffer[Long]): mutable.ArrayBuffer[Long] = {
    var out: mutable.ArrayBuffer[Long] = _copy_int_list(items)
    var i: Long = 0L
    while (i < __pytra_len(out)) {
        var j: Long = i + 1L
        while (j < __pytra_len(out)) {
            if (__pytra_int(__pytra_get_index(out, j)) < __pytra_int(__pytra_get_index(out, i))) {
                var tmp: Long = __pytra_int(__pytra_get_index(out, i))
                __pytra_set_index(out, i, __pytra_int(__pytra_get_index(out, j)))
                __pytra_set_index(out, j, tmp)
            }
            j += 1L
        }
        i += 1L
    }
    return out
}

def _register_type_node(type_id: Long, base_type_id: Long): Unit = {
    if (!_contains_int(_TYPE_IDS, type_id)) {
        _TYPE_IDS = __pytra_as_list(_TYPE_IDS); _TYPE_IDS.append(type_id)
    }
    __pytra_set_index(_TYPE_BASE, type_id, base_type_id)
    if (!__pytra_contains(_TYPE_CHILDREN, type_id)) {
        __pytra_set_index(_TYPE_CHILDREN, type_id, _make_int_list_0())
    }
    if (base_type_id < 0L) {
        return
    }
    if (!__pytra_contains(_TYPE_CHILDREN, base_type_id)) {
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, _make_int_list_0())
    }
    var children: Any = __pytra_get_index(_TYPE_CHILDREN, base_type_id)
    if (!_contains_int(children, type_id)) {
        children = __pytra_as_list(children); children.append(type_id)
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, children)
    }
}

def _sorted_child_type_ids(type_id: Long): mutable.ArrayBuffer[Long] = {
    var children: mutable.ArrayBuffer[Long] = _make_int_list_0()
    if (__pytra_contains(_TYPE_CHILDREN, type_id)) {
        children = __pytra_as_list(__pytra_get_index(_TYPE_CHILDREN, type_id)).asInstanceOf[mutable.ArrayBuffer[Long]]
    }
    return _sorted_ints(children)
}

def _collect_root_type_ids(): mutable.ArrayBuffer[Long] = {
    var roots: mutable.ArrayBuffer[Long] = __pytra_as_list(mutable.ArrayBuffer[Any]()).asInstanceOf[mutable.ArrayBuffer[Long]]
    var i: Long = 0L
    while (i < __pytra_len(_TYPE_IDS)) {
        var tid: Any = __pytra_get_index(_TYPE_IDS, i)
        var base_tid: Long = __pytra_int(-1L)
        if (__pytra_contains(_TYPE_BASE, tid)) {
            base_tid = __pytra_int(__pytra_get_index(_TYPE_BASE, tid))
        }
        if ((base_tid < 0L) || ((!__pytra_contains(_TYPE_BASE, base_tid)))) {
            roots.append(tid)
        }
        i += 1L
    }
    return _sorted_ints(roots)
}

def _assign_type_ranges_dfs(type_id: Long, next_order: Long): Long = {
    __pytra_set_index(_TYPE_ORDER, type_id, next_order)
    __pytra_set_index(_TYPE_MIN, type_id, next_order)
    var cur: Long = next_order + 1L
    var children: mutable.ArrayBuffer[Long] = _sorted_child_type_ids(type_id)
    var i: Long = 0L
    while (i < __pytra_len(children)) {
        cur = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(children, i)), cur)
        i += 1L
    }
    __pytra_set_index(_TYPE_MAX, type_id, cur - 1L)
    return cur
}

def _recompute_type_ranges(): Unit = {
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    var next_order: Long = 0L
    var roots: mutable.ArrayBuffer[Long] = _collect_root_type_ids()
    var i: Long = 0L
    while (i < __pytra_len(roots)) {
        next_order = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(roots, i)), next_order)
        i += 1L
    }
    var all_ids: mutable.ArrayBuffer[Long] = _sorted_ints(_TYPE_IDS)
    i = 0L
    while (i < __pytra_len(all_ids)) {
        var tid: Long = __pytra_int(__pytra_get_index(all_ids, i))
        if (!__pytra_contains(_TYPE_ORDER, tid)) {
            next_order = _assign_type_ranges_dfs(tid, next_order)
        }
        i += 1L
    }
}

def _mark_type_ranges_dirty(): Unit = {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1L)
}

def _mark_type_ranges_clean(): Unit = {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 0L)
}

def _is_type_ranges_dirty(): Boolean = {
    return (__pytra_int(__pytra_as_dict(_TYPE_STATE).getOrElse(__pytra_str("ranges_dirty"), 1L)) != 0L)
}

def _ensure_type_ranges(): Unit = {
    if (_is_type_ranges_dirty()) {
        _recompute_type_ranges()
        _mark_type_ranges_clean()
    }
}

def _ensure_builtins(): Unit = {
    if (!__pytra_contains(_TYPE_STATE, "next_user_type_id")) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    }
    if (!__pytra_contains(_TYPE_STATE, "ranges_dirty")) {
        __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1L)
    }
    if (__pytra_len(_TYPE_IDS) > 0L) {
        return
    }
    _register_type_node(_tid_none(), (-1L))
    _register_type_node(_tid_object(), (-1L))
    _register_type_node(_tid_int(), _tid_object())
    _register_type_node(_tid_bool(), _tid_int())
    _register_type_node(_tid_float(), _tid_object())
    _register_type_node(_tid_str(), _tid_object())
    _register_type_node(_tid_list(), _tid_object())
    _register_type_node(_tid_dict(), _tid_object())
    _register_type_node(_tid_set(), _tid_object())
    _recompute_type_ranges()
    _mark_type_ranges_clean()
}

def _normalize_base_type_id(base_type_id: Long): Long = {
    _ensure_builtins()
    if (!false) {
        throw new RuntimeException(__pytra_str("base type_id must be int"))
    }
    if (!__pytra_contains(_TYPE_BASE, base_type_id)) {
        throw new RuntimeException(__pytra_str(__pytra_str("unknown base type_id: ") + __pytra_str(base_type_id)))
    }
    return base_type_id
}

def py_tid_register_class_type(base_type_id: Long): Long = {
    _ensure_builtins()
    var base_tid: Long = _normalize_base_type_id(base_type_id)
    var tid: Any = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    while (__pytra_contains(_TYPE_BASE, tid)) {
        tid += 1L
    }
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", tid + 1L)
    _register_type_node(tid, base_tid)
    _mark_type_ranges_dirty()
    return __pytra_int(tid)
}

def py_tid_register_known_class_type(type_id: Long, base_type_id: Long): Long = {
    _ensure_builtins()
    if (!false) {
        throw new RuntimeException(__pytra_str("type_id must be int"))
    }
    if (type_id < _tid_user_base()) {
        throw new RuntimeException(__pytra_str(__pytra_str("user type_id must be >= ") + __pytra_str(_tid_user_base())))
    }
    var base_tid: Long = _normalize_base_type_id(base_type_id)
    if (__pytra_contains(_TYPE_BASE, type_id)) {
        if (__pytra_int(__pytra_get_index(_TYPE_BASE, type_id)) != base_tid) {
            throw new RuntimeException(__pytra_str("type_id already registered with different base"))
        }
        return type_id
    }
    _register_type_node(type_id, base_tid)
    var next_user_type_id: Any = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    if (type_id >= __pytra_int(next_user_type_id)) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", type_id + 1L)
    }
    _mark_type_ranges_dirty()
    return type_id
}

def _try_runtime_tagged_type_id(value: Any): Long = {
    var tagged: Long = __pytra_int(__pytra_any_default())
    if (false) {
        var tagged_id: Long = __pytra_int(tagged)
        if (__pytra_contains(_TYPE_BASE, tagged_id)) {
            return tagged_id
        }
    }
    return __pytra_int(-1L)
}

def py_tid_runtime_type_id(value: Any): Long = {
    _ensure_builtins()
    if (__pytra_float(value) == __pytra_float(__pytra_any_default())) {
        return _tid_none()
    }
    if (false) {
        return _tid_bool()
    }
    if (false) {
        return _tid_int()
    }
    if (false) {
        return _tid_float()
    }
    if (false) {
        return _tid_str()
    }
    if (false) {
        return _tid_list()
    }
    if (false) {
        return _tid_dict()
    }
    if (false) {
        return _tid_set()
    }
    var tagged: Long = _try_runtime_tagged_type_id(value)
    if (tagged >= 0L) {
        return tagged
    }
    return _tid_object()
}

def py_tid_is_subtype(actual_type_id: Long, expected_type_id: Long): Boolean = {
    _ensure_builtins()
    _ensure_type_ranges()
    if (!__pytra_contains(_TYPE_ORDER, actual_type_id)) {
        return false
    }
    if (!__pytra_contains(_TYPE_ORDER, expected_type_id)) {
        return false
    }
    var actual_order: Any = __pytra_get_index(_TYPE_ORDER, actual_type_id)
    var expected_min: Any = __pytra_get_index(_TYPE_MIN, expected_type_id)
    var expected_max: Any = __pytra_get_index(_TYPE_MAX, expected_type_id)
    return ((__pytra_float(expected_min) <= __pytra_float(actual_order)) && (__pytra_float(actual_order) <= __pytra_float(expected_max)))
}

def py_tid_issubclass(actual_type_id: Long, expected_type_id: Long): Boolean = {
    return __pytra_truthy(__pytra_any_default())
}

def py_tid_isinstance(value: Any, expected_type_id: Long): Boolean = {
    return __pytra_truthy(__pytra_any_default())
}

def _py_reset_type_registry_for_test(): Unit = {
    _TYPE_IDS.clear()
    _TYPE_BASE.clear()
    _TYPE_CHILDREN.clear()
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    _TYPE_STATE.clear()
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1L)
    _ensure_builtins()
}
