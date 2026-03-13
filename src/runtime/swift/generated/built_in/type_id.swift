// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/type_id.py
// generated-by: tools/gen_runtime_from_manifest.py

import Foundation


func _tid_none() -> Int64 {
    return Int64(0)
}

func _tid_bool() -> Int64 {
    return Int64(1)
}

func _tid_int() -> Int64 {
    return Int64(2)
}

func _tid_float() -> Int64 {
    return Int64(3)
}

func _tid_str() -> Int64 {
    return Int64(4)
}

func _tid_list() -> Int64 {
    return Int64(5)
}

func _tid_dict() -> Int64 {
    return Int64(6)
}

func _tid_set() -> Int64 {
    return Int64(7)
}

func _tid_object() -> Int64 {
    return Int64(8)
}

func _tid_user_base() -> Int64 {
    return Int64(1000)
}

func _make_int_list_0() -> [Any] {
    var out: [Any] = __pytra_as_list([])
    return out
}

func _make_int_list_1(_ a0: Int64) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    out.append(a0)
    return out
}

func _contains_int(_ items: [Any], _ value: Int64) -> Bool {
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(items))) {
        if (__pytra_int(__pytra_getIndex(items, i)) == __pytra_int(value)) {
            return true
        }
        i += Int64(1)
    }
    return false
}

func _copy_int_list(_ items: [Any]) -> [Any] {
    var out: [Any] = __pytra_as_list([])
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(items))) {
        out.append(__pytra_int(__pytra_getIndex(items, i)))
        i += Int64(1)
    }
    return out
}

func _sorted_ints(_ items: [Any]) -> [Any] {
    var out: [Any] = _copy_int_list(items)
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(out))) {
        var j: Int64 = (i + Int64(1))
        while (__pytra_int(j) < __pytra_int(__pytra_len(out))) {
            if (__pytra_int(__pytra_getIndex(out, j)) < __pytra_int(__pytra_getIndex(out, i))) {
                var tmp: Int64 = __pytra_int(__pytra_getIndex(out, i))
                let __idx_0 = Int(__pytra_index(__pytra_int(i), Int64(out.count)))
                if __idx_0 >= 0 && __idx_0 < out.count {
                    out[__idx_0] = __pytra_int(__pytra_getIndex(out, j))
                }
                let __idx_1 = Int(__pytra_index(__pytra_int(j), Int64(out.count)))
                if __idx_1 >= 0 && __idx_1 < out.count {
                    out[__idx_1] = tmp
                }
            }
            j += Int64(1)
        }
        i += Int64(1)
    }
    return out
}

func _register_type_node(_ type_id: Int64, _ base_type_id: Int64) {
    if (!_contains_int(_TYPE_IDS, type_id)) {
        _TYPE_IDS = __pytra_as_list(_TYPE_IDS); _TYPE_IDS.append(type_id)
    }
    __pytra_setIndex(_TYPE_BASE, type_id, base_type_id)
    if ((!__pytra_contains(_TYPE_CHILDREN, type_id))) {
        __pytra_setIndex(_TYPE_CHILDREN, type_id, _make_int_list_0())
    }
    if (__pytra_int(base_type_id) < __pytra_int(Int64(0))) {
        return
    }
    if ((!__pytra_contains(_TYPE_CHILDREN, base_type_id))) {
        __pytra_setIndex(_TYPE_CHILDREN, base_type_id, _make_int_list_0())
    }
    var children: Any = __pytra_getIndex(_TYPE_CHILDREN, base_type_id)
    if (!_contains_int(children, type_id)) {
        children = __pytra_as_list(children); children.append(type_id)
        __pytra_setIndex(_TYPE_CHILDREN, base_type_id, children)
    }
}

func _sorted_child_type_ids(_ type_id: Int64) -> [Any] {
    var children: [Any] = _make_int_list_0()
    if (__pytra_contains(_TYPE_CHILDREN, type_id)) {
        children = __pytra_as_list(__pytra_getIndex(_TYPE_CHILDREN, type_id))
    }
    return _sorted_ints(children)
}

func _collect_root_type_ids() -> [Any] {
    var roots: [Any] = __pytra_as_list([])
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(_TYPE_IDS))) {
        var tid: Any = __pytra_getIndex(_TYPE_IDS, i)
        var base_tid: Int64 = __pytra_int(-Int64(1))
        if (__pytra_contains(_TYPE_BASE, tid)) {
            base_tid = __pytra_int(__pytra_getIndex(_TYPE_BASE, tid))
        }
        if ((__pytra_int(base_tid) < __pytra_int(Int64(0))) || ((!__pytra_contains(_TYPE_BASE, base_tid)))) {
            roots.append(tid)
        }
        i += Int64(1)
    }
    return _sorted_ints(roots)
}

func _assign_type_ranges_dfs(_ type_id: Int64, _ next_order: Int64) -> Int64 {
    __pytra_setIndex(_TYPE_ORDER, type_id, next_order)
    __pytra_setIndex(_TYPE_MIN, type_id, next_order)
    var cur: Int64 = (next_order + Int64(1))
    var children: [Any] = _sorted_child_type_ids(type_id)
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(children))) {
        cur = _assign_type_ranges_dfs(__pytra_int(__pytra_getIndex(children, i)), cur)
        i += Int64(1)
    }
    __pytra_setIndex(_TYPE_MAX, type_id, (cur - Int64(1)))
    return cur
}

func _recompute_type_ranges() {
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    var next_order: Int64 = Int64(0)
    var roots: [Any] = _collect_root_type_ids()
    var i: Int64 = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(roots))) {
        next_order = _assign_type_ranges_dfs(__pytra_int(__pytra_getIndex(roots, i)), next_order)
        i += Int64(1)
    }
    var all_ids: [Any] = _sorted_ints(_TYPE_IDS)
    i = Int64(0)
    while (__pytra_int(i) < __pytra_int(__pytra_len(all_ids))) {
        var tid: Int64 = __pytra_int(__pytra_getIndex(all_ids, i))
        if ((!__pytra_contains(_TYPE_ORDER, tid))) {
            next_order = _assign_type_ranges_dfs(tid, next_order)
        }
        i += Int64(1)
    }
}

func _mark_type_ranges_dirty() {
    __pytra_setIndex(_TYPE_STATE, "ranges_dirty", Int64(1))
}

func _mark_type_ranges_clean() {
    __pytra_setIndex(_TYPE_STATE, "ranges_dirty", Int64(0))
}

func _is_type_ranges_dirty() -> Bool {
    return (__pytra_int(__pytra_dict_get(_TYPE_STATE, "ranges_dirty", Int64(1))) != __pytra_int(Int64(0)))
}

func _ensure_type_ranges() {
    if _is_type_ranges_dirty() {
        _recompute_type_ranges()
        _mark_type_ranges_clean()
    }
}

func _ensure_builtins() {
    if ((!__pytra_contains(_TYPE_STATE, "next_user_type_id"))) {
        __pytra_setIndex(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    }
    if ((!__pytra_contains(_TYPE_STATE, "ranges_dirty"))) {
        __pytra_setIndex(_TYPE_STATE, "ranges_dirty", Int64(1))
    }
    if (__pytra_int(__pytra_len(_TYPE_IDS)) > __pytra_int(Int64(0))) {
        return
    }
    _register_type_node(_tid_none(), (-Int64(1)))
    _register_type_node(_tid_object(), (-Int64(1)))
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

func _normalize_base_type_id(_ base_type_id: Int64) -> Int64 {
    _ensure_builtins()
    if (!false) {
        fatalError("pytra raise")
    }
    if ((!__pytra_contains(_TYPE_BASE, base_type_id))) {
        fatalError("pytra raise")
    }
    return base_type_id
}

func py_tid_register_class_type(_ base_type_id: Int64) -> Int64 {
    _ensure_builtins()
    var base_tid: Int64 = _normalize_base_type_id(base_type_id)
    var tid: Any = __pytra_getIndex(_TYPE_STATE, "next_user_type_id")
    while (__pytra_contains(_TYPE_BASE, tid)) {
        tid += Int64(1)
    }
    __pytra_setIndex(_TYPE_STATE, "next_user_type_id", (tid + Int64(1)))
    _register_type_node(tid, base_tid)
    _mark_type_ranges_dirty()
    return __pytra_int(tid)
}

func py_tid_register_known_class_type(_ type_id: Int64, _ base_type_id: Int64) -> Int64 {
    _ensure_builtins()
    if (!false) {
        fatalError("pytra raise")
    }
    if (__pytra_int(type_id) < __pytra_int(_tid_user_base())) {
        fatalError("pytra raise")
    }
    var base_tid: Int64 = _normalize_base_type_id(base_type_id)
    if (__pytra_contains(_TYPE_BASE, type_id)) {
        if (__pytra_int(__pytra_getIndex(_TYPE_BASE, type_id)) != __pytra_int(base_tid)) {
            fatalError("pytra raise")
        }
        return type_id
    }
    _register_type_node(type_id, base_tid)
    var next_user_type_id: Any = __pytra_getIndex(_TYPE_STATE, "next_user_type_id")
    if (__pytra_int(type_id) >= __pytra_int(next_user_type_id)) {
        __pytra_setIndex(_TYPE_STATE, "next_user_type_id", (type_id + Int64(1)))
    }
    _mark_type_ranges_dirty()
    return type_id
}

func _try_runtime_tagged_type_id(_ value: Any) -> Int64 {
    var tagged: Int64 = __pytra_int(__pytra_any_default())
    if false {
        var tagged_id: Int64 = __pytra_int(tagged)
        if (__pytra_contains(_TYPE_BASE, tagged_id)) {
            return tagged_id
        }
    }
    return __pytra_int(-Int64(1))
}

func py_tid_runtime_type_id(_ value: Any) -> Int64 {
    _ensure_builtins()
    if (__pytra_float(value) == __pytra_float(__pytra_any_default())) {
        return _tid_none()
    }
    if false {
        return _tid_bool()
    }
    if false {
        return _tid_int()
    }
    if false {
        return _tid_float()
    }
    if false {
        return _tid_str()
    }
    if false {
        return _tid_list()
    }
    if false {
        return _tid_dict()
    }
    if false {
        return _tid_set()
    }
    var tagged: Int64 = _try_runtime_tagged_type_id(value)
    if (__pytra_int(tagged) >= __pytra_int(Int64(0))) {
        return tagged
    }
    return _tid_object()
}

func py_tid_is_subtype(_ actual_type_id: Int64, _ expected_type_id: Int64) -> Bool {
    _ensure_builtins()
    _ensure_type_ranges()
    if ((!__pytra_contains(_TYPE_ORDER, actual_type_id))) {
        return false
    }
    if ((!__pytra_contains(_TYPE_ORDER, expected_type_id))) {
        return false
    }
    var actual_order: Any = __pytra_getIndex(_TYPE_ORDER, actual_type_id)
    var expected_min: Any = __pytra_getIndex(_TYPE_MIN, expected_type_id)
    var expected_max: Any = __pytra_getIndex(_TYPE_MAX, expected_type_id)
    return ((__pytra_float(expected_min) <= __pytra_float(actual_order)) && (__pytra_float(actual_order) <= __pytra_float(expected_max)))
}

func py_tid_issubclass(_ actual_type_id: Int64, _ expected_type_id: Int64) -> Bool {
    return __pytra_truthy(__pytra_any_default())
}

func py_tid_isinstance(_ value: Any, _ expected_type_id: Int64) -> Bool {
    return __pytra_truthy(__pytra_any_default())
}

func _py_reset_type_registry_for_test() {
    _TYPE_IDS.clear()
    _TYPE_BASE.clear()
    _TYPE_CHILDREN.clear()
    _TYPE_ORDER.clear()
    _TYPE_MIN.clear()
    _TYPE_MAX.clear()
    _TYPE_STATE.clear()
    __pytra_setIndex(_TYPE_STATE, "next_user_type_id", _tid_user_base())
    __pytra_setIndex(_TYPE_STATE, "ranges_dirty", Int64(1))
    _ensure_builtins()
}
