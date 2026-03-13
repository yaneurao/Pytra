// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py



fun _tid_none(): Long {
    return 0L
}

fun _tid_bool(): Long {
    return 1L
}

fun _tid_int(): Long {
    return 2L
}

fun _tid_float(): Long {
    return 3L
}

fun _tid_str(): Long {
    return 4L
}

fun _tid_list(): Long {
    return 5L
}

fun _tid_dict(): Long {
    return 6L
}

fun _tid_set(): Long {
    return 7L
}

fun _tid_object(): Long {
    return 8L
}

fun _tid_user_base(): Long {
    return 1000L
}

fun _make_int_list_0(): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    return out
}

fun _make_int_list_1(a0: Long): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    out.add(a0)
    return out
}

fun _contains_int(items: MutableList<Any?>, value: Long): Boolean {
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(items)))) {
        if ((__pytra_int(__pytra_get_index(items, i)) == __pytra_int(value))) {
            return true
        }
        i += 1L
    }
    return false
}

fun _copy_int_list(items: MutableList<Any?>): MutableList<Any?> {
    var out: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(items)))) {
        out.add(__pytra_int(__pytra_get_index(items, i)))
        i += 1L
    }
    return out
}

fun _sorted_ints(items: MutableList<Any?>): MutableList<Any?> {
    var out: MutableList<Any?> = _copy_int_list(items)
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(out)))) {
        var j: Long = (i + 1L)
        while ((__pytra_int(j) < __pytra_int(__pytra_len(out)))) {
            if ((__pytra_int(__pytra_get_index(out, j)) < __pytra_int(__pytra_get_index(out, i)))) {
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

fun _register_type_node(type_id: Long, base_type_id: Long) {
    if ((!_contains_int(_TYPE_IDS, type_id))) {
        _TYPE_IDS = __pytra_as_list(_TYPE_IDS); _TYPE_IDS.add(type_id)
    }
    __pytra_set_index(_TYPE_BASE, type_id, base_type_id)
    if (((!__pytra_contains(_TYPE_CHILDREN, type_id)))) {
        __pytra_set_index(_TYPE_CHILDREN, type_id, _make_int_list_0())
    }
    if ((__pytra_int(base_type_id) < __pytra_int(0L))) {
        return
    }
    if (((!__pytra_contains(_TYPE_CHILDREN, base_type_id)))) {
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, _make_int_list_0())
    }
    var children: Any? = __pytra_get_index(_TYPE_CHILDREN, base_type_id)
    if ((!_contains_int(children, type_id))) {
        children = __pytra_as_list(children); children.add(type_id)
        __pytra_set_index(_TYPE_CHILDREN, base_type_id, children)
    }
}

fun _sorted_child_type_ids(type_id: Long): MutableList<Any?> {
    var children: MutableList<Any?> = _make_int_list_0()
    if ((__pytra_contains(_TYPE_CHILDREN, type_id))) {
        children = __pytra_as_list(__pytra_get_index(_TYPE_CHILDREN, type_id))
    }
    return _sorted_ints(children)
}

fun _collect_root_type_ids(): MutableList<Any?> {
    var roots: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(_TYPE_IDS)))) {
        var tid: Any? = __pytra_get_index(_TYPE_IDS, i)
        var base_tid: Long = __pytra_int(-1L)
        if ((__pytra_contains(_TYPE_BASE, tid))) {
            base_tid = __pytra_int(__pytra_get_index(_TYPE_BASE, tid))
        }
        if (((__pytra_int(base_tid) < __pytra_int(0L)) || ((!__pytra_contains(_TYPE_BASE, base_tid))))) {
            roots.add(tid)
        }
        i += 1L
    }
    return _sorted_ints(roots)
}

fun _assign_type_ranges_dfs(type_id: Long, next_order: Long): Long {
    __pytra_set_index(_TYPE_ORDER, type_id, next_order)
    __pytra_set_index(_TYPE_MIN, type_id, next_order)
    var cur: Long = (next_order + 1L)
    var children: MutableList<Any?> = _sorted_child_type_ids(type_id)
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(children)))) {
        cur = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(children, i)), cur)
        i += 1L
    }
    __pytra_set_index(_TYPE_MAX, type_id, (cur - 1L))
    return cur
}

fun _recompute_type_ranges() {
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    var next_order: Long = 0L
    var roots: MutableList<Any?> = _collect_root_type_ids()
    var i: Long = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(roots)))) {
        next_order = _assign_type_ranges_dfs(__pytra_int(__pytra_get_index(roots, i)), next_order)
        i += 1L
    }
    var all_ids: MutableList<Any?> = _sorted_ints(_TYPE_IDS)
    i = 0L
    while ((__pytra_int(i) < __pytra_int(__pytra_len(all_ids)))) {
        var tid: Long = __pytra_int(__pytra_get_index(all_ids, i))
        if (((!__pytra_contains(_TYPE_ORDER, tid)))) {
            next_order = _assign_type_ranges_dfs(tid, next_order)
        }
        i += 1L
    }
}

fun _mark_type_ranges_dirty() {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1L)
}

fun _mark_type_ranges_clean() {
    __pytra_set_index(_TYPE_STATE, "ranges_dirty", 0L)
}

fun _is_type_ranges_dirty(): Boolean {
    return (__pytra_int(_TYPE_STATE.get("ranges_dirty") ?: 1L) != __pytra_int(0L))
}

fun _ensure_type_ranges() {
    if (_is_type_ranges_dirty()) {
        _recompute_type_ranges()
        _mark_type_ranges_clean()
    }
}

fun _ensure_builtins() {
    if (((!__pytra_contains(_TYPE_STATE, "next_user_type_id")))) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    }
    if (((!__pytra_contains(_TYPE_STATE, "ranges_dirty")))) {
        __pytra_set_index(_TYPE_STATE, "ranges_dirty", 1L)
    }
    if ((__pytra_int(__pytra_len(_TYPE_IDS)) > __pytra_int(0L))) {
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

fun _normalize_base_type_id(base_type_id: Long): Long {
    _ensure_builtins()
    if ((!false)) {
        throw RuntimeException(__pytra_str("base type_id must be int"))
    }
    if (((!__pytra_contains(_TYPE_BASE, base_type_id)))) {
        throw RuntimeException(__pytra_str((__pytra_str("unknown base type_id: ") + __pytra_str(base_type_id))))
    }
    return base_type_id
}

fun py_tid_register_class_type(base_type_id: Long): Long {
    _ensure_builtins()
    var base_tid: Long = _normalize_base_type_id(base_type_id)
    var tid: Any? = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    while ((__pytra_contains(_TYPE_BASE, tid))) {
        tid += 1L
    }
    __pytra_set_index(_TYPE_STATE, "next_user_type_id", (tid + 1L))
    _register_type_node(tid, base_tid)
    _mark_type_ranges_dirty()
    return __pytra_int(tid)
}

fun py_tid_register_known_class_type(type_id: Long, base_type_id: Long): Long {
    _ensure_builtins()
    if ((!false)) {
        throw RuntimeException(__pytra_str("type_id must be int"))
    }
    if ((__pytra_int(type_id) < __pytra_int(_tid_user_base()))) {
        throw RuntimeException(__pytra_str((__pytra_str("user type_id must be >= ") + __pytra_str(_tid_user_base()))))
    }
    var base_tid: Long = _normalize_base_type_id(base_type_id)
    if ((__pytra_contains(_TYPE_BASE, type_id))) {
        if ((__pytra_int(__pytra_get_index(_TYPE_BASE, type_id)) != __pytra_int(base_tid))) {
            throw RuntimeException(__pytra_str("type_id already registered with different base"))
        }
        return type_id
    }
    _register_type_node(type_id, base_tid)
    var next_user_type_id: Any? = __pytra_get_index(_TYPE_STATE, "next_user_type_id")
    if ((__pytra_int(type_id) >= __pytra_int(next_user_type_id))) {
        __pytra_set_index(_TYPE_STATE, "next_user_type_id", (type_id + 1L))
    }
    _mark_type_ranges_dirty()
    return type_id
}

fun _try_runtime_tagged_type_id(value: Any): Long {
    var tagged: Long = __pytra_int(__pytra_any_default())
    if (false) {
        var tagged_id: Long = __pytra_int(tagged)
        if ((__pytra_contains(_TYPE_BASE, tagged_id))) {
            return tagged_id
        }
    }
    return __pytra_int(-1L)
}

fun py_tid_runtime_type_id(value: Any): Long {
    _ensure_builtins()
    if ((__pytra_float(value) == __pytra_float(__pytra_any_default()))) {
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
    if ((__pytra_int(tagged) >= __pytra_int(0L))) {
        return tagged
    }
    return _tid_object()
}

fun py_tid_is_subtype(actual_type_id: Long, expected_type_id: Long): Boolean {
    _ensure_builtins()
    _ensure_type_ranges()
    if (((!__pytra_contains(_TYPE_ORDER, actual_type_id)))) {
        return false
    }
    if (((!__pytra_contains(_TYPE_ORDER, expected_type_id)))) {
        return false
    }
    var actual_order: Any? = __pytra_get_index(_TYPE_ORDER, actual_type_id)
    var expected_min: Any? = __pytra_get_index(_TYPE_MIN, expected_type_id)
    var expected_max: Any? = __pytra_get_index(_TYPE_MAX, expected_type_id)
    return ((__pytra_float(expected_min) <= __pytra_float(actual_order)) && (__pytra_float(actual_order) <= __pytra_float(expected_max)))
}

fun py_tid_issubclass(actual_type_id: Long, expected_type_id: Long): Boolean {
    return __pytra_truthy(__pytra_any_default())
}

fun py_tid_isinstance(value: Any, expected_type_id: Long): Boolean {
    return __pytra_truthy(__pytra_any_default())
}

fun _py_reset_type_registry_for_test() {
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
